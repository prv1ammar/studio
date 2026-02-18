"""
Asana Integration Node - Studio Standard
Part of Phase 6: Rewriting Existing Nodes to remove Composio
"""
import json
import httpx
from typing import Any, Dict, Optional, List
from ..base import BaseNode
from ..registry import register_node

@register_node("asana_node")
class AsanaNode(BaseNode):
    """
    Interact with Asanadirectly via REST API.
    Supports: Create Task, Get Task, List Projects, List Workspaces.
    Replaces Composio Asana implementation.
    """
    node_type = "asana_node"
    version = "1.0.0"
    category = "productivity"
    credentials_required = ["asana_auth"]


    properties = [
        {
            'displayName': 'Operation',
            'name': 'operation',
            'type': 'options',
            'default': 'get_task',
            'options': [
                {'name': 'Get Task', 'value': 'get_task'},
                {'name': 'Create Task', 'value': 'create_task'},
                {'name': 'List Projects', 'value': 'list_projects'},
                {'name': 'List Workspaces', 'value': 'list_workspaces'},
            ],
            'description': 'Action to perform',
        },
        {
            'displayName': 'Name',
            'name': 'name',
            'type': 'string',
            'default': '',
            'description': 'Task name',
        },
        {
            'displayName': 'Notes',
            'name': 'notes',
            'type': 'string',
            'default': '',
            'description': 'Task description/notes',
        },
        {
            'displayName': 'Project Id',
            'name': 'project_id',
            'type': 'string',
            'default': '',
            'description': 'Asana Project GID',
        },
        {
            'displayName': 'Task Id',
            'name': 'task_id',
            'type': 'string',
            'default': '',
            'description': 'Asana Task GID',
        },
        {
            'displayName': 'Workspace Id',
            'name': 'workspace_id',
            'type': 'string',
            'default': '',
            'description': 'Asana Workspace GID',
        },
    ]
    inputs = {
        "action": {
            "type": "dropdown",
            "default": "get_task",
            "options": [
                "get_task",
                "create_task",
                "list_projects",
                "list_workspaces"
            ],
            "description": "Action to perform"
        },
        "task_id": {
            "type": "string",
            "optional": True,
            "description": "Asana Task GID"
        },
        "workspace_id": {
            "type": "string",
            "optional": True,
            "description": "Asana Workspace GID"
        },
        "project_id": {
            "type": "string",
            "optional": True,
            "description": "Asana Project GID"
        },
        "name": {
            "type": "string",
            "optional": True,
            "description": "Task name"
        },
        "notes": {
            "type": "string",
            "optional": True,
            "description": "Task description/notes"
        }
    }

    outputs = {
        "result": {"type": "json"},
        "gid": {"type": "string"},
        "name": {"type": "string"},
        "status": {"type": "string"}
    }

    async def execute(self, input_data: Any, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        try:
            # 1. Get Credentials
            creds = await self.get_credential("asana_auth")
            token = None
            if creds:
                token = creds.get("token") or creds.get("personal_access_token") or creds.get("access_token")
            
            if not token:
                token = self.get_config("api_key")
            
            if not token:
                return {"status": "error", "error": "Asana Personal Access Token is required."}

            # 2. Setup Client
            headers = {
                "Authorization": f"Bearer {token}",
                "Accept": "application/json"
            }
            
            base_url = "https://app.asana.com/api/1.0"
            action = self.get_config("action", "get_task")
            
            async with httpx.AsyncClient(headers=headers, timeout=30.0) as client:
                
                result_data = {}
                
                if action == "get_task":
                    task_id = self.get_config("task_id") or (input_data if isinstance(input_data, str) else None)
                    if not task_id:
                         return {"status": "error", "error": "Task ID is required for get_task."}
                    
                    resp = await client.get(f"{base_url}/tasks/{task_id}")
                    resp.raise_for_status()
                    result_data = resp.json().get("data", {})

                elif action == "create_task":
                    workspace = self.get_config("workspace_id")
                    name = self.get_config("name") or (input_data if isinstance(input_data, str) else "New Task from Studio")
                    notes = self.get_config("notes") or ""
                    projects = self.get_config("project_id")
                    
                    if not workspace:
                        return {"status": "error", "error": "Workspace ID is required for creating a task."}
                    
                    payload = {
                        "data": {
                            "workspace": workspace,
                            "name": name,
                            "notes": notes
                        }
                    }
                    if projects:
                        payload["data"]["projects"] = [projects]
                        
                    resp = await client.post(f"{base_url}/tasks", json=payload)
                    resp.raise_for_status()
                    result_data = resp.json().get("data", {})

                elif action == "list_workspaces":
                    resp = await client.get(f"{base_url}/workspaces")
                    resp.raise_for_status()
                    workspaces = resp.json().get("data", [])
                    result_data = {"workspaces": workspaces, "count": len(workspaces)}

                elif action == "list_projects":
                    workspace = self.get_config("workspace_id")
                    if workspace:
                        resp = await client.get(f"{base_url}/projects?workspace={workspace}")
                    else:
                        resp = await client.get(f"{base_url}/projects")
                    resp.raise_for_status()
                    projects = resp.json().get("data", [])
                    result_data = {"projects": projects, "count": len(projects)}
                
                else:
                    return {"status": "error", "error": f"Unknown action: {action}"}

                return {
                    "status": "success",
                    "data": {
                        "result": result_data,
                        "gid": result_data.get("gid"),
                        "name": result_data.get("name"),
                        "status": "completed"
                    }
                }

        except httpx.HTTPStatusError as e:
            return {"status": "error", "error": f"Asana API Error ({e.response.status_code}): {e.response.text}"}
        except Exception as e:
            return {"status": "error", "error": f"Asana Node execution failed: {str(e)}"}