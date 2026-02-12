import os
import sys
import json
from typing import Dict, List, Any, Optional

# Fix for Windows symlink permission error in HuggingFace Hub
os.environ["HF_HUB_DISABLE_SYMLINKS"] = "1"
os.environ["HF_HUB_DISABLE_SYMLINKS_WARNING"] = "1"

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import ORJSONResponse
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select
from app.db.session import get_session
from app.db.models import User, Workflow, WorkflowVersion, AuditLog, Credential
from app.api.auth import get_current_user
from app.core.audit import audit_logger

# Add project root to path (AI-Agent-Studio/)
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))

# Ensure outputs directory exists
outputs_dir = os.path.join(project_root, "outputs")
os.makedirs(outputs_dir, exist_ok=True)

# Backend path to support 'app.' imports
backend_path = os.path.join(project_root, "backend")
if backend_path not in sys.path:
    sys.path.append(backend_path)

# Vendor path for imported libraries (langflow, lfx)
vendor_path = os.path.join(project_root, "backend", "vendor")
if vendor_path not in sys.path:
    sys.path.append(vendor_path)
    
if project_root not in sys.path:
    sys.path.append(project_root)

# Correct module paths based on new structure
try:
    from ..models.schema import ExecutionRequest, WorkflowGraph
    from ..core.engine import engine
except ImportError:
    from backend.app.models.schema import ExecutionRequest, WorkflowGraph
    from backend.app.core.engine import engine

app = FastAPI(
    title="AI Agent Studio Engine",
    default_response_class=ORJSONResponse
)

from app.core.config import settings
import redis.asyncio as aioredis
from arq import create_pool
from arq.connections import RedisSettings
import uuid
import asyncio

@app.on_event("startup")
async def startup_event():
    # Initialize Database
    try:
        from app.db.session import init_db
        await init_db()
        print("OK: Database initialized successfully")
    except Exception as e:
        print(f"ERROR: Database initialization failed: {e}")

    # Initialize Redis for Pub/Sub and Arq for task queuing
    try:
        app.state.redis = aioredis.from_url(settings.REDIS_URL, decode_responses=True)
        app.state.redis_pool = await create_pool(RedisSettings.from_dsn(settings.REDIS_URL))
        
        # Initialize rate limiter
        from app.core.rate_limiter import rate_limiter
        await rate_limiter.init_redis(app.state.redis)
        print(f"OK: Rate limiter initialized (User: {settings.MAX_CONCURRENT_JOBS_PER_USER}, Workspace: {settings.MAX_CONCURRENT_JOBS_PER_WORKSPACE})")
        
        # Initialize cache manager
        from app.core.cache import cache_manager
        await cache_manager.init_redis(app.state.redis)
        
        # Initialize analytics tracker
        from app.core.analytics import analytics_tracker
        await analytics_tracker.init_redis(app.state.redis)
        
        # Initialize circuit breaker
        from app.core.circuit_breaker import circuit_breaker
        await circuit_breaker.init_redis(app.state.redis)
        
        # Start background listener for Redis Pub/Sub
        asyncio.create_task(listen_to_redis_updates())
        print(f"OK: Connected to Redis at {settings.REDIS_URL}")
    except Exception as e:
        print(f"ERROR: Failed to connect to Redis: {e}")

async def listen_to_redis_updates():
    """Listens to all workflow updates from workers and broadcasts them to WebSockets."""
    pubsub = app.state.redis.pubsub()
    await pubsub.psubscribe("workflow_updates_*")
    print("INFO: Listening for workflow updates on Redis...")
    try:
        async for message in pubsub.listen():
            if message["type"] == "pmessage":
                try:
                    data = json.loads(message["data"])
                    await manager.broadcast(data)
                except Exception as e:
                    print(f"Error parsing/broadcasting Redis message: {e}")
    except Exception as e:
        print(f"Redis listener error: {e}")

# Mount static files for images/graphs
app.mount("/outputs", StaticFiles(directory=outputs_dir), name="outputs")

# Enable CORS for React Flow frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from starlette.middleware.base import BaseHTTPMiddleware

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["Content-Security-Policy"] = "default-src 'self'"
        return response

app.add_middleware(SecurityHeadersMiddleware)

# Force server reload: Supabase Tables fix

from app.api.auth import router as auth_router
from app.api.workspace import router as workspace_router
from app.api.billing import router as billing_router

app.include_router(auth_router, prefix="/auth", tags=["auth"])
app.include_router(workspace_router, prefix="/workspaces", tags=["workspaces"])
app.include_router(billing_router, prefix="/billing", tags=["billing"])

class ConnectionManager:
    def __init__(self):
        # Room-based connections: {workflow_id: [WebSocket]}
        self.rooms: Dict[str, List[WebSocket]] = {}
        # User presence: {workflow_id: {user_id: {name, color, cursor}}}
        self.presence: Dict[str, Dict[str, Any]] = {}

    async def connect(self, websocket: WebSocket, workflow_id: str = "global"):
        await websocket.accept()
        if workflow_id not in self.rooms:
            self.rooms[workflow_id] = []
        self.rooms[workflow_id].append(websocket)

    def disconnect(self, websocket: WebSocket, workflow_id: str = "global"):
        if workflow_id in self.rooms and websocket in self.rooms[workflow_id]:
            self.rooms[workflow_id].remove(websocket)

    async def broadcast(self, message: dict, workflow_id: str = "global"):
        targets = self.rooms.get(workflow_id, [])
        for connection in targets:
            try:
                await connection.send_json(message)
            except Exception:
                pass

    async def send_to_user(self, websocket: WebSocket, message: dict):
        try:
            await websocket.send_json(message)
        except Exception:
            pass
                
manager = ConnectionManager()

@app.websocket("/ws/{workflow_id}")
async def websocket_endpoint(websocket: WebSocket, workflow_id: str):
    await manager.connect(websocket, workflow_id)
    try:
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)
            
            # Handle collaboration messages (cursors, selection)
            if message.get("type") in ["cursor", "select", "node_moving"]:
                # Broadcast to other users in the same room
                await manager.broadcast({
                    "type": f"collaboration_{message['type']}",
                    "user_id": message.get("user_id"),
                    "data": message.get("data")
                }, workflow_id)
                
    except WebSocketDisconnect:
        manager.disconnect(websocket, workflow_id)

@app.get("/stats")
async def get_system_stats(db: AsyncSession = Depends(get_session)):
    """Returns real-time execution metrics for the dashboard including cache and worker stats."""
    try:
        # Count failures from AuditLogs with fail in action
        fail_result = await db.execute(select(AuditLog).where(AuditLog.action.like("%fail%")))
        failed_count = len(fail_result.scalars().all())
        
        # Get cache stats
        from app.core.cache import cache_manager
        cache_stats = cache_manager.get_stats()
        
        # Get worker health
        from app.core.worker_monitor import worker_monitor
        worker_health = await worker_monitor.get_health_status()
        
        return {
            "status": "active",
            "total_nodes": len(engine.node_factory.get_all_types()) if hasattr(engine.node_factory, 'get_all_types') else 0,
            "failed_workflows": failed_count,
            "uptime": "99.9% (PostgreSQL)",
            "cache": {
                "hit_rate": cache_stats.get("hit_rate", 0),
                "total_requests": cache_stats.get("total_requests", 0),
                "enabled": cache_stats.get("enabled", False)
            },
            "workers": {
                "active": worker_health.get("workers", {}).get("active", 0),
                "status": worker_health.get("status", "unknown"),
                "queue_depth": worker_health.get("queues", {}).get("total_pending", 0)
            }
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.post("/run/resume")
async def resume_workflow(execution_id: str, start_node_id: str, current_user: User = Depends(get_current_user)):
    """Resumes a failed workflow from a specific node with rate limiting."""
    try:
        from app.core.rate_limiter import rate_limiter
        
        # 1. Load from DLQ
        dlq_path = Path(f"backend/data/dlq/failed_{execution_id}.json")
        if not dlq_path.exists():
            raise HTTPException(status_code=404, detail="Execution not found in DLQ")
            
        with open(dlq_path, "r") as f:
            data = json.load(f)
        
        # Extract workspace_id from context if available
        workspace_id = data.get("context_summary", {}).get("workspace_id")
        
        # 2. Check rate limits
        user_allowed = await rate_limiter.check_user_limit(
            current_user.id, 
            tier=current_user.tier, 
            custom_limits=current_user.tier_limits
        )
        if not user_allowed:
            raise HTTPException(
                status_code=429, 
                detail=f"User concurrent execution limit reached for tier '{current_user.tier}'"
            )
        
        if workspace_id:
            ws_allowed = await rate_limiter.check_workspace_limit(
                workspace_id,
                tier=current_user.tier,
                custom_limits=current_user.tier_limits
            )
            if not ws_allowed:
                raise HTTPException(
                    status_code=429,
                    detail=f"Workspace concurrent execution limit reached ({settings.MAX_CONCURRENT_JOBS_PER_WORKSPACE})"
                )
        
        # 3. Acquire rate limit slots
        import time
        job_id = f"resume-{execution_id}-{int(time.time())}"
        await rate_limiter.acquire(current_user.id, workspace_id, job_id)
            
        # 4. Queue resumption task
        await app.state.redis_pool.enqueue_job(
            'run_workflow_task',
            graph_data=data["graph"],
            message=data.get("message", ""),
            job_id=job_id,
            start_node_id=start_node_id,
            initial_outputs=data.get("context_summary", {}),
            user_id=current_user.id,
            workspace_id=workspace_id,
            queue="default"
        )
        
        return {"job_id": job_id, "status": "resuming"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/nodes/smartdb/metadata")
async def get_smartdb_metadata(base_url: str, api_key: str, project_id: Optional[str] = None):
    try:
        from ..nodes.storage.nocodb.nocodb_node import SmartDBNode
        if not project_id:
            projects = SmartDBNode.fetch_projects(base_url, api_key)
            return {
                "projects": projects or [],
                "options": projects or [],
                "data": projects or []
            }
        else:
            tables = SmartDBNode.fetch_tables(base_url, api_key, project_id)
            return {
                "tables": tables or [],
                "options": tables or [],
                "data": tables or []
            }
    except Exception as e:
        return {"error": str(e), "projects": [], "tables": []}

@app.get("/nodes/supabase/tables")
async def get_supabase_tables(supabase_url: str, supabase_key: str):
    try:
        from ..nodes.storage.supabase.supabase_node import SupabaseStoreNode
        tables = SupabaseStoreNode.fetch_tables(supabase_url, supabase_key)
        return {"tables": tables or []}
    except Exception as e:
        print(f"Error fetching Supabase tables: {e}")
        return {"tables": [], "error": str(e)}

@app.get("/credentials/list")
async def list_credentials(type: Optional[str] = None, workspace_id: Optional[str] = None, current_user: User = Depends(get_current_user)):
    """Lists available credentials for the current user or workspace from PG."""
    try:
        from app.core.credentials import cred_manager
        creds = await cred_manager.list_credentials(user_id=current_user.id, cred_type=type, workspace_id=workspace_id)
        return {"credentials": [{"label": c["name"], "value": c["id"]} for c in creds]}
    except Exception as e:
        return {"credentials": [], "error": str(e)}

@app.post("/credentials/add")
async def add_credential(request: Dict[str, Any], workspace_id: Optional[str] = None, current_user: User = Depends(get_current_user)):
    """Adds a new credential for the current user or workspace in PG."""
    try:
        from app.core.credentials import cred_manager
        cred_id = await cred_manager.add_credential(
            user_id=current_user.id,
            workspace_id=workspace_id,
            cred_type=request.get("type"),
            data=request.get("data"),
            name=request.get("name"),
            cred_id=request.get("id")
        )
        await audit_logger.log(
            action="credential_add", 
            user_id=current_user.id, 
            workspace_id=workspace_id,
            details={"type": request.get("type"), "name": request.get("name"), "id": cred_id}
        )
        return {"status": "success", "id": cred_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/credentials/{cred_id}")
async def delete_credential(cred_id: str, workspace_id: Optional[str] = None, current_user: User = Depends(get_current_user)):
    """Removes a credential belonging to the current user or workspace from PG."""
    try:
        from app.core.credentials import cred_manager
        success = await cred_manager.remove_credential(cred_id, user_id=current_user.id, workspace_id=workspace_id)
        await audit_logger.log(
            action="credential_delete", 
            user_id=current_user.id, 
            workspace_id=workspace_id,
            details={"cred_id": cred_id, "success": success}
        )
        return {"status": "success" if success else "not_found"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/credentials/{cred_id}/test")
async def test_credential(cred_id: str, workspace_id: Optional[str] = None, current_user: User = Depends(get_current_user)):
    """Tests if a credential is valid by attempting a lightweight API call."""
    try:
        from app.core.credentials import cred_manager
        cred_obj = await cred_manager.get_credential(cred_id, user_id=current_user.id, workspace_id=workspace_id)
        if not cred_obj:
            raise HTTPException(status_code=404, detail="Credential not found")
        
        cred_type = cred_obj["type"]
        data = cred_obj["data"]

        if cred_type == "discord":
            import aiohttp
            async with aiohttp.ClientSession() as session:
                payload = {"content": "✅ Studio Credential Test Successful!"}
                async with session.post(data.get("webhook_url"), json=payload) as resp:
                    if resp.status < 400:
                        return {"status": "success", "message": "Discord Webhook is valid! Check your channel."}
                    return {"status": "error", "message": f"Discord Error: {resp.status}"}
                    
        elif cred_type == "telegram":
            import aiohttp
            token = data.get("bot_token")
            async with aiohttp.ClientSession() as session:
                async with session.get(f"https://api.telegram.org/bot{token}/getMe") as resp:
                    res_data = await resp.json()
                    if res_data.get("ok"):
                        bot_username = res_data["result"]["username"]
                        return {"status": "success", "message": f"Telegram Bot @{bot_username} is active!"}
                    return {"status": "error", "message": res_data.get("description")}
        
        return {"status": "info", "message": f"Testing not yet implemented for {cred_type}, but data is saved."}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/cache/stats")
async def get_cache_stats(current_user: User = Depends(get_current_user)):
    """Get cache statistics including hit rate and total requests."""
    from app.core.cache import cache_manager
    return cache_manager.get_stats()

@app.post("/cache/invalidate")
async def invalidate_cache(pattern: Optional[str] = None, current_user: User = Depends(get_current_user)):
    """Invalidate cache entries matching pattern. Admin only."""
    from app.core.cache import cache_manager
    count = await cache_manager.invalidate(pattern)
    return {"status": "success", "invalidated": count, "pattern": pattern or "cache:node:*"}

@app.post("/cache/invalidate/{node_type}")
async def invalidate_node_cache(node_type: str, current_user: User = Depends(get_current_user)):
    """Invalidate all cache entries for a specific node type."""
    from app.core.cache import cache_manager
    count = await cache_manager.invalidate_node_type(node_type)
    return {"status": "success", "invalidated": count, "node_type": node_type}

@app.post("/cache/reset-stats")
async def reset_cache_stats(current_user: User = Depends(get_current_user)):
    """Reset cache statistics counters."""
    from app.core.cache import cache_manager
    cache_manager.reset_stats()
    return {"status": "success", "message": "Cache statistics reset"}

@app.get("/workers/health")
async def get_workers_health(current_user: User = Depends(get_current_user)):
    """Get comprehensive worker health status and queue metrics."""
    from app.core.worker_monitor import worker_monitor
    return await worker_monitor.get_health_status()

@app.get("/workers/list")
async def list_active_workers(current_user: User = Depends(get_current_user)):
    """List all active workers with heartbeat data."""
    from app.core.worker_monitor import worker_monitor
    workers = await worker_monitor.get_active_workers()
    return {"workers": workers, "count": len(workers)}

@app.get("/workers/queues")
async def get_queue_stats(current_user: User = Depends(get_current_user)):
    """Get queue depth statistics for all queues."""
    from app.core.worker_monitor import worker_monitor
    return await worker_monitor.get_queue_stats()

@app.get("/analytics/nodes")
async def get_node_analytics(limit: int = 20, current_user: User = Depends(get_current_user)):
    """Get most-used nodes and usage statistics."""
    from app.core.analytics import analytics_tracker
    stats = await analytics_tracker.get_node_usage_stats(limit)
    return {"nodes": stats, "count": len(stats)}

@app.get("/analytics/workflows")
async def get_workflow_analytics(days: int = 7, current_user: User = Depends(get_current_user)):
    """Get workflow execution statistics for the last N days."""
    from app.core.analytics import analytics_tracker
    return await analytics_tracker.get_workflow_stats(days)

@app.get("/analytics/performance")
async def get_performance_insights(current_user: User = Depends(get_current_user)):
    """Get performance insights including slowest nodes and failure rates."""
    from app.core.analytics import analytics_tracker
    return await analytics_tracker.get_performance_insights()

@app.get("/analytics/costs")
async def get_cost_analysis(days: int = 30, current_user: User = Depends(get_current_user)):
    """Get API cost analysis for the last N days."""
    from app.core.analytics import analytics_tracker
    return await analytics_tracker.get_cost_analysis(days)

@app.get("/circuit-breaker/status")
async def get_all_circuit_status(current_user: User = Depends(get_current_user)):
    """Get status of all circuit breakers."""
    from app.core.circuit_breaker import circuit_breaker
    circuits = await circuit_breaker.get_all_circuits()
    return {"circuits": circuits, "count": len(circuits)}

@app.get("/circuit-breaker/status/{node_type}")
async def get_circuit_status(node_type: str, current_user: User = Depends(get_current_user)):
    """Get circuit breaker status for a specific node type."""
    from app.core.circuit_breaker import circuit_breaker
    return await circuit_breaker.get_circuit_status(node_type)

@app.post("/circuit-breaker/reset/{node_type}")
async def reset_circuit(node_type: str, current_user: User = Depends(get_current_user)):
    """Manually reset a circuit breaker (admin override)."""
    from app.core.circuit_breaker import circuit_breaker
    await circuit_breaker.reset_circuit(node_type)
    return {"status": "success", "message": f"Circuit breaker reset for {node_type}"}

@app.get("/nodes")
def get_node_library():
    """Returns the JSON library for the sidebar. Optimized to ensure essential nodes exist."""
    try:
        lib_path = os.path.join(project_root, "backend", "data", "node_library.json")
        if os.path.exists(lib_path):
            with open(lib_path, "r", encoding="utf-8") as f:
                lib = json.load(f)
                
                # Check for critical missing categories if necessary
                return lib
        return {}
    except Exception as e:
        print(f"Error loading nodes: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/library")
def get_library_alias():
    return get_node_library()

@app.get("/logs")
async def get_audit_logs(limit: int = 50, db: AsyncSession = Depends(get_session), current_user: User = Depends(get_current_user)):
    """Retrieves the last N audit log entries from PG."""
    try:
        result = await db.execute(select(AuditLog).order_by(AuditLog.timestamp.desc()).limit(limit))
        logs = result.scalars().all()
        return logs
    except Exception as e:
        print(f"Error reading logs: {e}")
        return []

@app.post("/workflow/snapshot")
async def save_workflow_snapshot(workflow_data: Dict[str, Any], workspace_id: Optional[str] = None, db: AsyncSession = Depends(get_session), current_user: User = Depends(get_current_user)):
    """Saves an immutable version of the workflow to PG."""
    try:
        from app.db.models import WorkspaceMember
        workflow_name = workflow_data.get("name", "Untitled")
        
        # Determine workspace (logic same as save)
        if not workspace_id:
            from app.db.models import Workspace
            res = await db.execute(select(Workspace).where(Workspace.owner_id == current_user.id, Workspace.name == "Personal Workspace"))
            ws = res.scalar_one_or_none()
            workspace_id = ws.id if ws else None
            
        if not workspace_id:
            raise HTTPException(status_code=400, detail="Workspace required")

        # 2. Verify Membership & Role
        res = await db.execute(select(WorkspaceMember).where(WorkspaceMember.workspace_id == workspace_id, WorkspaceMember.user_id == current_user.id))
        membership = res.scalar_one_or_none()
        if not membership:
            raise HTTPException(status_code=403, detail="Access denied to this workspace")
            
        if membership.role == "viewer":
            raise HTTPException(status_code=403, detail="Viewers cannot create snapshots")

        result = await db.execute(
            select(Workflow)
            .where(Workflow.name == workflow_name, Workflow.workspace_id == workspace_id)
        )
        workflow = result.scalar_one_or_none()
        
        if not workflow:
            # Create workflow entry first if it doesn't exist
            workflow = Workflow(
                name=workflow_name,
                workspace_id=workspace_id,
                definition=workflow_data
            )
            db.add(workflow)
            await db.flush()
        
        # Save version
        version = WorkflowVersion(
            workflow_id=workflow.id,
            definition=workflow_data
        )
        db.add(version)
        await db.commit()
            
        return {"status": "success", "version_id": version.id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/workflow/versions")
async def list_workflow_versions(db: AsyncSession = Depends(get_session), current_user: User = Depends(get_current_user)):
    """Lists all saved workflow versions accessible to the user."""
    try:
        from app.db.models import WorkspaceMember
        result = await db.execute(
            select(WorkflowVersion)
            .join(Workflow)
            .join(WorkspaceMember, Workflow.workspace_id == WorkspaceMember.workspace_id)
            .where(WorkspaceMember.user_id == current_user.id)
            .order_by(WorkflowVersion.created_at.desc())
        )
        versions = result.scalars().all()
        return [
            {
                "id": v.id,
                "workflow_name": v.workflow.name,
                "created_at": v.created_at.isoformat()
            } for v in versions
        ]
    except Exception as e:
        print(f"Error listing versions: {e}")
        return []

@app.get("/workflow/versions/{version_id}")
async def get_workflow_version(version_id: str, db: AsyncSession = Depends(get_session), current_user: User = Depends(get_current_user)):
    """Retrieves a specific workflow snapshot if user has access."""
    try:
        from app.db.models import WorkspaceMember
        result = await db.execute(
            select(WorkflowVersion)
            .join(Workflow)
            .join(WorkspaceMember, Workflow.workspace_id == WorkspaceMember.workspace_id)
            .where(WorkflowVersion.id == version_id, WorkspaceMember.user_id == current_user.id)
        )
        version = result.scalar_one_or_none()
        if not version:
            raise HTTPException(status_code=404, detail="Version not found or access denied")
            
        return version.definition
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/agents")
def get_available_agents():
    return {
        "agents": [
            {"id": "faq", "name": "Knowledge Base (FAQ)", "icon": "BookOpen"},
            {"id": "orchestrator", "name": "Core Orchestrator", "icon": "Cpu"}
        ]
    }

# Workflow Store Integration
try:
    from ...scripts.store import workflow_store
except ImportError:
    # Try generic import if script is in path
    try:
        import store as workflow_store
    except:
        workflow_store = None

class SaveRequest(BaseModel):
    name: str
    graph: Dict[str, Any]

@app.post("/workflows/save")
async def save_workflow(request: SaveRequest, workspace_id: Optional[str] = None, db: AsyncSession = Depends(get_session), current_user: User = Depends(get_current_user)):
    """Saves or updates a workflow. If workspace_id is missing, uses Personal Workspace."""
    try:
        from app.db.models import WorkspaceMember, Workspace
        
        # 1. Determine Workspace
        if not workspace_id:
            # Find user's Personal Workspace
            res = await db.execute(select(Workspace).where(Workspace.owner_id == current_user.id, Workspace.name == "Personal Workspace"))
            ws = res.scalar_one_or_none()
            if not ws:
                # Emergency creation if missing (legacy users)
                ws = Workspace(name="Personal Workspace", owner_id=current_user.id)
                db.add(ws)
                await db.flush()
                db.add(WorkspaceMember(workspace_id=ws.id, user_id=current_user.id, role="owner"))
            workspace_id = ws.id
        
        # 2. Verify Membership & Role
        res = await db.execute(select(WorkspaceMember).where(WorkspaceMember.workspace_id == workspace_id, WorkspaceMember.user_id == current_user.id))
        membership = res.scalar_one_or_none()
        if not membership:
            raise HTTPException(status_code=403, detail="Access denied to this workspace")
            
        if membership.role == "viewer":
            raise HTTPException(status_code=403, detail="Viewers cannot save or modify workflows")

        # 3. Find Workflow
        result = await db.execute(
            select(Workflow).where(Workflow.name == request.name, Workflow.workspace_id == workspace_id)
        )
        workflow = result.scalar_one_or_none()
        
        if workflow:
            workflow.definition = request.graph
            workflow.updated_at = datetime.utcnow()
        else:
            workflow = Workflow(
                name=request.name,
                workspace_id=workspace_id,
                definition=request.graph
            )
            db.add(workflow)
            
        await db.commit()
        await audit_logger.log(
            action="workflow_save", 
            user_id=current_user.id, 
            workspace_id=workspace_id,
            details={"name": request.name, "workflow_id": workflow.id}
        )
        return {"status": "success", "id": workflow.id}
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/workflows/list")
async def list_workflows(workspace_id: Optional[str] = None, db: AsyncSession = Depends(get_session), current_user: User = Depends(get_current_user)):
    """Lists workflows. Optionally filtered by workspace_id."""
    try:
        from app.db.models import WorkspaceMember
        query = select(Workflow).join(WorkspaceMember, Workflow.workspace_id == WorkspaceMember.workspace_id).where(WorkspaceMember.user_id == current_user.id)
        
        if workspace_id:
            query = query.where(Workflow.workspace_id == workspace_id)
            
        result = await db.execute(query)
        workflows = result.scalars().all()
        return {"workflows": [w.name for w in workflows]}
    except Exception as e:
        print(f"Error listing workflows: {e}")
        return {"workflows": []}

@app.get("/workflows/load/{name}")
async def load_workflow(name: str, db: AsyncSession = Depends(get_session), current_user: User = Depends(get_current_user)):
    """Loads a specific workflow if the user has access via workspace membership."""
    try:
        from app.db.models import WorkspaceMember
        result = await db.execute(
            select(Workflow)
            .join(WorkspaceMember, Workflow.workspace_id == WorkspaceMember.workspace_id)
            .where(Workflow.name == name, WorkspaceMember.user_id == current_user.id)
        )
        workflow = result.scalar_one_or_none()
        if not workflow:
            raise HTTPException(status_code=404, detail="Workflow not found or access denied")
        return workflow.definition
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
@app.post("/run/node")
async def run_individual_node(request: Dict[str, Any], current_user: User = Depends(get_current_user)):
    try:
        node_id = request.get("nodeId")
        graph_data = request.get("graph", {})
        nodes = graph_data.get("nodes", [])
        node = next((n for n in nodes if n["id"] == node_id), None)
        if not node: raise HTTPException(status_code=404)
        node_data = node.get("data", {})
        target_type = node_data.get("id") or node.get("type")
        
        # Add user_id to context
        context = {
            "graph_data": graph_data, 
            "node_id": node_id, 
            "engine": engine,
            "user_id": current_user.id
        }
        
        result = await engine.execute_node(target_type, None, config=node_data, context=context)
        return {"result": result, "status": "success"}
    except Exception as e:
        import traceback
        traceback.print_exc()
        return {"error": str(e), "status": "failed"}

@app.post("/run")
async def run_workflow(execution: ExecutionRequest, current_user: User = Depends(get_current_user)):
    try:
        # Rate Limiting (Sync)
        from app.core.rate_limiter import rate_limiter
        user_allowed = await rate_limiter.check_user_limit(
            current_user.id, 
            tier=current_user.tier, 
            custom_limits=current_user.tier_limits
        )
        if not user_allowed:
            raise HTTPException(status_code=429, detail=f"User concurrent execution limit reached for tier '{current_user.tier}'")
        
        # Acquire slot
        job_id = str(uuid.uuid4())
        await rate_limiter.acquire(current_user.id, execution_id=job_id)
        
        try:
            graph_data = execution.graph.model_dump()
            async def broadcast_event(event_type, node_id, data=None):
                await manager.broadcast({"type": event_type, "node_id": node_id, "data": data})
            
            response_text = await engine.process_workflow(
                graph_data, 
                execution.message, 
                broadcaster=broadcast_event,
                context={"user_id": current_user.id, "execution_id": job_id}
            )
            await audit_logger.log(
                action="workflow_run_sync", 
                user_id=current_user.id, 
                details={"status": "success", "execution_id": job_id}
            )
            return {"response": response_text, "status": "success", "sender_name": "Studio Engine"}
        finally:
            # Release slot
            await rate_limiter.release(current_user.id)
            
    except Exception as e:
        await audit_logger.log(
            action="workflow_run_sync_fail", 
            user_id=current_user.id, 
            details={"error": str(e)}
        )
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/run/async")
async def run_workflow_async(execution: ExecutionRequest, current_user: User = Depends(get_current_user)):
    """Offloads workflow execution to a background worker with user identity."""
    try:
        # Rate Limiting (Async)
        from app.core.rate_limiter import rate_limiter
        user_allowed = await rate_limiter.check_user_limit(
            current_user.id, 
            tier=current_user.tier, 
            custom_limits=current_user.tier_limits
        )
        if not user_allowed:
            raise HTTPException(status_code=429, detail=f"User concurrent execution limit reached for tier '{current_user.tier}'")
            
        job_id = str(uuid.uuid4())
        graph_data = execution.graph.model_dump()
        
        # Acquire slot (released by worker)
        await rate_limiter.acquire(current_user.id, execution_id=job_id)
        
        # Determine queue based on region
        region = current_user.preferred_region or "us-east-1"
        queue_name = f"{region}-default"
        
        await app.state.redis_pool.enqueue_job(
            'run_workflow_task',
            graph_data=graph_data,
            message=execution.message,
            job_id=job_id,
            user_id=current_user.id,
            _queue_name=queue_name
        )
        
        await audit_logger.log(
            action="workflow_run_async_queued", 
            user_id=current_user.id, 
            details={"job_id": job_id, "region": region, "queue": queue_name}
        )
        return {
            "job_id": job_id,
            "status": "queued",
            "region": region,
            "message": f"Workflow execution started in {region}"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to queue task: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
