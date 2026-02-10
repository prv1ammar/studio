import os
import sys
import json
from typing import Dict, List, Any, Optional

# Fix for Windows symlink permission error in HuggingFace Hub
os.environ["HF_HUB_DISABLE_SYMLINKS"] = "1"
os.environ["HF_HUB_DISABLE_SYMLINKS_WARNING"] = "1"

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

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

app = FastAPI(title="AI Agent Studio Engine")

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

@app.get("/health")
def health():
    return {"status": "online", "engine": "FastAPI + ReactFlow Migration"}

@app.get("/debug/paths")
def debug_paths():
    return {
        "sys_path": sys.path,
        "project_root": project_root,
        "cwd": os.getcwd()
    }

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
async def list_credentials(type: Optional[str] = None):
    """Lists available credentials. Returns metadata only (data removed for safety if needed, but here we return names)."""
    try:
        from app.core.credentials import cred_manager
        creds = cred_manager.list_credentials(cred_type=type)
        return {"credentials": [{"label": c["name"], "value": c["id"]} for c in creds]}
    except Exception as e:
        return {"credentials": [], "error": str(e)}

@app.post("/credentials/add")
async def add_credential(request: Dict[str, Any]):
    """Adds a new credential to the store."""
    try:
        from app.core.credentials import cred_manager
        cred_id = cred_manager.add_credential(
            cred_id=request.get("id"),
            cred_type=request.get("type"),
            data=request.get("data"),
            name=request.get("name")
        )
        return {"status": "success", "id": cred_id}
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
async def save_workflow(request: SaveRequest):
    if not workflow_store: return {"error": "Store not available"}
    return workflow_store.save_workflow(request.name, request.graph)

@app.get("/workflows/list")
async def list_workflows():
    if not workflow_store: return {"workflows": []}
    return {"workflows": workflow_store.list_workflows()}

@app.get("/workflows/load/{filename}")
async def load_workflow(filename: str):
    if not workflow_store: raise HTTPException(status_code=404)
    data = workflow_store.load_workflow(filename)
    if not data: raise HTTPException(status_code=404)
    return data

@app.post("/run/node")
async def run_individual_node(request: Dict[str, Any]):
    try:
        node_id = request.get("nodeId")
        graph_data = request.get("graph", {})
        nodes = graph_data.get("nodes", [])
        node = next((n for n in nodes if n["id"] == node_id), None)
        if not node: raise HTTPException(status_code=404)
        node_data = node.get("data", {})
        target_type = node_data.get("id") or node.get("type")
        result = await engine.execute_node(target_type, None, config=node_data, context={"graph_data": graph_data, "node_id": node_id, "engine": engine})
        return {"result": result, "status": "success"}
    except Exception as e:
        import traceback
        traceback.print_exc()
        return {"error": str(e), "status": "failed"}

@app.post("/run")
async def run_workflow(execution: ExecutionRequest):
    try:
        graph_data = execution.graph.model_dump()
        async def broadcast_event(event_type, node_id, data=None):
            await manager.broadcast({"type": event_type, "nodeId": node_id, "data": data})
        response_text = await engine.process_workflow(graph_data, execution.message, broadcaster=broadcast_event)
        return {"response": response_text, "status": "success", "sender_name": "Studio Engine"}
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
