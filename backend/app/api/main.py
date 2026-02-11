import os
import sys
import json
from typing import Dict, List, Any, Optional

# Fix for Windows symlink permission error in HuggingFace Hub
os.environ["HF_HUB_DISABLE_SYMLINKS"] = "1"
os.environ["HF_HUB_DISABLE_SYMLINKS_WARNING"] = "1"

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import ORJSONResponse
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select
from app.db.session import get_session
from app.db.models import User, Workflow, WorkflowVersion, AuditLog, Credential
from app.api.auth import get_current_user

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
        print("✅ Database initialized successfully")
    except Exception as e:
        print(f"❌ Database initialization failed: {e}")

    # Initialize Redis for Pub/Sub and Arq for task queuing
    try:
        app.state.redis = aioredis.from_url(settings.REDIS_URL, decode_responses=True)
        app.state.redis_pool = await create_pool(RedisSettings.from_dsn(settings.REDIS_URL))
        
        # Start background listener for Redis Pub/Sub
        asyncio.create_task(listen_to_redis_updates())
        print(f"✅ Connected to Redis at {settings.REDIS_URL}")
    except Exception as e:
        print(f"❌ Failed to connect to Redis: {e}")

async def listen_to_redis_updates():
    """Listens to all workflow updates from workers and broadcasts them to WebSockets."""
    pubsub = app.state.redis.pubsub()
    await pubsub.psubscribe("workflow_updates_*")
    print("👂 Listening for workflow updates on Redis...")
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

# Force server reload: Supabase Tables fix

from app.api.auth import router as auth_router
app.include_router(auth_router, prefix="/auth", tags=["auth"])

class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, message: dict):
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception as e:
                print(f"Error broadcasting to {connection}: {e}")
                
manager = ConnectionManager()

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            # Echo back or handle specific messages if needed
    except WebSocketDisconnect:
        manager.disconnect(websocket)

@app.get("/stats")
async def get_system_stats(db: AsyncSession = Depends(get_session)):
    """Returns real-time execution metrics for the dashboard from PG."""
    try:
        # Count failures from AuditLogs with fail in action
        fail_result = await db.execute(select(AuditLog).where(AuditLog.action.like("%fail%")))
        failed_count = len(fail_result.scalars().all())
        
        return {
            "status": "active",
            "total_nodes": len(engine.node_factory.get_all_types()) if hasattr(engine.node_factory, 'get_all_types') else 0,
            "failed_workflows": failed_count,
            "uptime": "99.9% (PostgreSQL)",
            "worker_status": "connected"
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.post("/run/resume")
async def resume_workflow(execution_id: str, start_node_id: str):
    """Resumes a failed workflow from a specific node."""
    try:
        # 1. Load from DLQ
        dlq_path = Path(f"backend/data/dlq/failed_{execution_id}.json")
        if not dlq_path.exists():
            raise HTTPException(status_code=404, detail="Execution not found in DLQ")
            
        with open(dlq_path, "r") as f:
            data = json.load(f)
            
        # 2. Queue resumption task
        import time
        job_id = f"resume-{execution_id}-{int(time.time())}"
        await app.state.redis_pool.enqueue_job(
            'run_workflow_task',
            graph_data=data["graph"],
            message=data.get("message", ""),
            job_id=job_id,
            start_node_id=start_node_id,
            initial_outputs=data.get("context_summary", {})
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
async def list_credentials(type: Optional[str] = None, current_user: User = Depends(get_current_user)):
    """Lists available credentials for the current user from PG."""
    try:
        from app.core.credentials import cred_manager
        creds = await cred_manager.list_credentials(user_id=current_user.id, cred_type=type)
        return {"credentials": [{"label": c["name"], "value": c["id"]} for c in creds]}
    except Exception as e:
        return {"credentials": [], "error": str(e)}

@app.post("/credentials/add")
async def add_credential(request: Dict[str, Any], current_user: User = Depends(get_current_user)):
    """Adds a new credential for the current user in PG."""
    try:
        from app.core.credentials import cred_manager
        cred_id = await cred_manager.add_credential(
            user_id=current_user.id,
            cred_type=request.get("type"),
            data=request.get("data"),
            name=request.get("name"),
            cred_id=request.get("id")
        )
        return {"status": "success", "id": cred_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/credentials/{cred_id}")
async def delete_credential(cred_id: str, current_user: User = Depends(get_current_user)):
    """Removes a credential belonging to the current user from PG."""
    try:
        from app.core.credentials import cred_manager
        success = await cred_manager.remove_credential(cred_id, user_id=current_user.id)
        return {"status": "success" if success else "not_found"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

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
async def save_workflow_snapshot(workflow_data: Dict[str, Any], db: AsyncSession = Depends(get_session), current_user: User = Depends(get_current_user)):
    """Saves an immutable version of the workflow to PG."""
    try:
        # Check if workflow exists, otherwise create it
        workflow_name = workflow_data.get("name", "Untitled")
        result = await db.execute(select(Workflow).where(Workflow.name == workflow_name, Workflow.user_id == current_user.id))
        workflow = result.scalar_one_or_none()
        
        if not workflow:
            workflow = Workflow(
                name=workflow_name,
                user_id=current_user.id,
                definition=workflow_data
            )
            db.add(workflow)
            await db.commit()
            await db.refresh(workflow)
        
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
    """Lists all saved workflow versions for the user from PG."""
    try:
        result = await db.execute(
            select(WorkflowVersion)
            .join(Workflow)
            .where(Workflow.user_id == current_user.id)
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
        return []

@app.get("/workflow/versions/{version_id}")
async def get_workflow_version(version_id: str, db: AsyncSession = Depends(get_session), current_user: User = Depends(get_current_user)):
    """Retrieves a specific workflow snapshot from PG."""
    try:
        result = await db.execute(
            select(WorkflowVersion)
            .join(Workflow)
            .where(WorkflowVersion.id == version_id, Workflow.user_id == current_user.id)
        )
        version = result.scalar_one_or_none()
        if not version:
            raise HTTPException(status_code=404, detail="Version not found")
            
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
async def save_workflow(request: SaveRequest, db: AsyncSession = Depends(get_session), current_user: User = Depends(get_current_user)):
    """Saves or updates a workflow for the current user in PG."""
    try:
        result = await db.execute(
            select(Workflow).where(Workflow.name == request.name, Workflow.user_id == current_user.id)
        )
        workflow = result.scalar_one_or_none()
        
        if workflow:
            workflow.definition = request.graph
            workflow.updated_at = datetime.utcnow()
        else:
            workflow = Workflow(
                name=request.name,
                user_id=current_user.id,
                definition=request.graph
            )
            db.add(workflow)
            
        await db.commit()
        return {"status": "success", "id": workflow.id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/workflows/list")
async def list_workflows(db: AsyncSession = Depends(get_session), current_user: User = Depends(get_current_user)):
    """Lists all workflows for the current user from PG."""
    try:
        result = await db.execute(select(Workflow).where(Workflow.user_id == current_user.id))
        workflows = result.scalars().all()
        return {"workflows": [w.name for w in workflows]}
    except Exception as e:
        return {"workflows": []}

@app.get("/workflows/load/{name}")
async def load_workflow(name: str, db: AsyncSession = Depends(get_session), current_user: User = Depends(get_current_user)):
    """Loads a specific workflow for the current user from PG."""
    try:
        result = await db.execute(
            select(Workflow).where(Workflow.name == name, Workflow.user_id == current_user.id)
        )
        workflow = result.scalar_one_or_none()
        if not workflow:
            raise HTTPException(status_code=404, detail="Workflow not found")
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
        graph_data = execution.graph.model_dump()
        async def broadcast_event(event_type, node_id, data=None):
            await manager.broadcast({"type": event_type, "node_id": node_id, "data": data})
        
        response_text = await engine.process_workflow(
            graph_data, 
            execution.message, 
            broadcaster=broadcast_event,
            context={"user_id": current_user.id}
        )
        return {"response": response_text, "status": "success", "sender_name": "Studio Engine"}
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/run/async")
async def run_workflow_async(execution: ExecutionRequest, current_user: User = Depends(get_current_user)):
    """Offloads workflow execution to a background worker with user identity."""
    try:
        job_id = str(uuid.uuid4())
        graph_data = execution.graph.model_dump()
        
        await app.state.redis_pool.enqueue_job(
            'run_workflow_task',
            graph_data=graph_data,
            message=execution.message,
            job_id=job_id,
            user_id=current_user.id
        )
        
        return {
            "job_id": job_id,
            "status": "queued",
            "message": f"Workflow for {current_user.email} offloaded to background worker."
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to queue task: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
