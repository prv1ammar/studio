"""
Asana Node - Studio Standard
Batch 69: Project Collaboration
"""
from typing import Any, Dict, Optional, List
import aiohttp
from ..base import BaseNode
from ..registry import register_node

@register_node("asana_node")
class AsanaNode(BaseNode):
    """
    Automate task and project management via Asana.
    """
    node_type = "asana_node"
    version = "1.0.0"
    category = "collaboration"
    credentials_required = ["asana_auth"]


    properties = [
        {
            'displayName': 'Operation',
            'name': 'operation',
            'type': 'options',
            'default': 'list_tasks',
            'options': [
                {'name': 'List Tasks', 'value': 'list_tasks'},
                {'name': 'Create Task', 'value': 'create_task'},
                {'name': 'Get Task', 'value': 'get_task'},
                {'name': 'List Projects', 'value': 'list_projects'},
                {'name': 'List Workspaces', 'value': 'list_workspaces'},
            ],
            'description': 'Asana action',
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
            'description': 'GID of the project',
        },
        {
            'displayName': 'Task Id',
            'name': 'task_id',
            'type': 'string',
            'default': '',
        },
        {
            'displayName': 'Workspace Id',
            'name': 'workspace_id',
            'type': 'string',
            'default': '',
            'description': 'GID of the workspace',
        },
    ]
    inputs = {
        "action": {
            "type": "dropdown",
            "default": "list_tasks",
            "options": ["list_tasks", "create_task", "get_task", "list_projects", "list_workspaces"],
            "description": "Asana action"
        },
        "project_id": {
            "type": "string",
            "optional": True,
            "description": "GID of the project"
        },
        "workspace_id": {
            "type": "string",
            "optional": True,
            "description": "GID of the workspace"
        },
        "task_id": {
            "type": "string",
            "optional": True
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
        "result": {"type": "any"},
        "status": {"type": "string"},
        "count": {"type": "number"}
    }

    async def execute(self, input_data: Any, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        try:
            creds = await self.get_credential("asana_auth")
            access_token = creds.get("access_token") if creds else self.get_config("access_token")
            
            if not access_token:
                return {"status": "error", "error": "Asana Access Token is required."}

            headers = {
                "Authorization": f"Bearer {access_token}",
                "Accept": "application/json",
                "Content-Type": "application/json"
            }
            
            base_url = "https://app.asana.com/api/1.0"
            action = self.get_config("action", "list_tasks")

            async with aiohttp.ClientSession() as session:
                if action == "list_workspaces":
                    async with session.get(f"{base_url}/workspaces", headers=headers) as resp:
                        res_data = await resp.json()
                        data = res_data.get("data", [])
                        return {"status": "success", "data": {"result": data, "count": len(data)}}

                elif action == "list_projects":
                    workspace_id = self.get_config("workspace_id")
                    url = f"{base_url}/projects"
                    params = {"workspace": workspace_id} if workspace_id else {}
                    async with session.get(url, headers=headers, params=params) as resp:
                        res_data = await resp.json()
                        data = res_data.get("data", [])
                        return {"status": "success", "data": {"result": data, "count": len(data)}}

                elif action == "list_tasks":
                    project_id = self.get_config("project_id")
                    if not project_id:
                         return {"status": "error", "error": "project_id is required to list tasks."}
                    url = f"{base_url}/tasks"
                    params = {"project": project_id}
                    async with session.get(url, headers=headers, params=params) as resp:
                        res_data = await resp.json()
                        data = res_data.get("data", [])
                        return {"status": "success", "data": {"result": data, "count": len(data)}}

                elif action == "get_task":
                    task_id = self.get_config("task_id") or str(input_data)
                    async with session.get(f"{base_url}/tasks/{task_id}", headers=headers) as resp:
                        res_data = await resp.json()
                        return {"status": "success", "data": {"result": res_data.get("data")}}

                elif action == "create_task":
                    name = self.get_config("name") or str(input_data)
                    workspace_id = self.get_config("workspace_id")
                    projects = [self.get_config("project_id")] if self.get_config("project_id") else []
                    
                    payload = {
                        "data": {
                            "name": name,
                            "notes": self.get_config("notes", ""),
                            "projects": projects
                        }
                    }
                    if workspace_id:
                        payload["data"]["workspace"] = workspace_id
                        
                    async with session.post(f"{base_url}/tasks", headers=headers, json=payload) as resp:
                        res_data = await resp.json()
                        return {"status": "success", "data": {"result": res_data.get("data"), "status": "created"}}

                return {"status": "error", "error": f"Unsupported action: {action}"}

        except Exception as e:
            return {"status": "error", "error": f"Asana Node Failed: {str(e)}"}