"""
ClickUp Node - Studio Standard
Batch 69: Project Collaboration
"""
from typing import Any, Dict, Optional, List
import aiohttp
from ..base import BaseNode
from ..registry import register_node

@register_node("clickup_node")
class ClickUpNode(BaseNode):
    """
    Automate work management via the ClickUp API.
    """
    node_type = "clickup_node"
    version = "1.0.0"
    category = "collaboration"
    credentials_required = ["clickup_auth"]


    properties = [
        {
            'displayName': 'Operation',
            'name': 'operation',
            'type': 'options',
            'default': 'list_tasks',
            'options': [
                {'name': 'List Tasks', 'value': 'list_tasks'},
                {'name': 'Create Task', 'value': 'create_task'},
                {'name': 'List Folders', 'value': 'list_folders'},
                {'name': 'List Lists', 'value': 'list_lists'},
                {'name': 'Get Teams', 'value': 'get_teams'},
            ],
            'description': 'ClickUp action',
        },
        {
            'displayName': 'Description',
            'name': 'description',
            'type': 'string',
            'default': '',
        },
        {
            'displayName': 'List Id',
            'name': 'list_id',
            'type': 'string',
            'default': '',
        },
        {
            'displayName': 'Name',
            'name': 'name',
            'type': 'string',
            'default': '',
            'description': 'Task name',
        },
        {
            'displayName': 'Space Id',
            'name': 'space_id',
            'type': 'string',
            'default': '',
        },
        {
            'displayName': 'Team Id',
            'name': 'team_id',
            'type': 'string',
            'default': '',
            'description': 'ID of the team/workspace',
        },
    ]
    inputs = {
        "action": {
            "type": "dropdown",
            "default": "list_tasks",
            "options": ["list_tasks", "create_task", "list_folders", "list_lists", "get_teams"],
            "description": "ClickUp action"
        },
        "team_id": {
            "type": "string",
            "optional": True,
            "description": "ID of the team/workspace"
        },
        "space_id": {
            "type": "string",
            "optional": True
        },
        "list_id": {
            "type": "string",
            "optional": True
        },
        "name": {
            "type": "string",
            "optional": True,
            "description": "Task name"
        },
        "description": {
            "type": "string",
            "optional": True
        }
    }

    outputs = {
        "result": {"type": "any"},
        "status": {"type": "string"},
        "count": {"type": "number"}
    }

    async def execute(self, input_data: Any, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        try:
            creds = await self.get_credential("clickup_auth")
            access_token = creds.get("api_key") if creds else self.get_config("api_key")
            
            if not access_token:
                return {"status": "error", "error": "ClickUp API Key/Token is required."}

            headers = {
                "Authorization": access_token,
                "Content-Type": "application/json"
            }
            
            base_url = "https://api.clickup.com/api/v2"
            action = self.get_config("action", "list_tasks")

            async with aiohttp.ClientSession() as session:
                if action == "get_teams":
                    async with session.get(f"{base_url}/team", headers=headers) as resp:
                        res_data = await resp.json()
                        teams = res_data.get("teams", [])
                        return {"status": "success", "data": {"result": teams, "count": len(teams)}}

                elif action == "list_folders":
                    space_id = self.get_config("space_id")
                    if not space_id:
                        return {"status": "error", "error": "space_id is required to list folders."}
                    async with session.get(f"{base_url}/space/{space_id}/folder", headers=headers) as resp:
                        res_data = await resp.json()
                        folders = res_data.get("folders", [])
                        return {"status": "success", "data": {"result": folders, "count": len(folders)}}

                elif action == "list_lists":
                    folder_id = self.get_config("folder_id") # Note: can also be on space level
                    space_id = self.get_config("space_id")
                    if folder_id:
                        url = f"{base_url}/folder/{folder_id}/list"
                    elif space_id:
                        url = f"{base_url}/space/{space_id}/list"
                    else:
                        return {"status": "error", "error": "folder_id or space_id is required to list lists."}
                        
                    async with session.get(url, headers=headers) as resp:
                        res_data = await resp.json()
                        lists = res_data.get("lists", [])
                        return {"status": "success", "data": {"result": lists, "count": len(lists)}}

                elif action == "list_tasks":
                    list_id = self.get_config("list_id")
                    if not list_id:
                        return {"status": "error", "error": "list_id is required to list tasks."}
                    async with session.get(f"{base_url}/list/{list_id}/task", headers=headers) as resp:
                        res_data = await resp.json()
                        tasks = res_data.get("tasks", [])
                        return {"status": "success", "data": {"result": tasks, "count": len(tasks)}}

                elif action == "create_task":
                    list_id = self.get_config("list_id")
                    if not list_id:
                        return {"status": "error", "error": "list_id is required to create a task."}
                    
                    name = self.get_config("name") or str(input_data)
                    payload = {
                        "name": name,
                        "description": self.get_config("description", ""),
                        "status": "to do"
                    }
                    async with session.post(f"{base_url}/list/{list_id}/task", headers=headers, json=payload) as resp:
                        res_data = await resp.json()
                        return {"status": "success", "data": {"result": res_data, "status": "created"}}

                return {"status": "error", "error": f"Unsupported action: {action}"}

        except Exception as e:
            return {"status": "error", "error": f"ClickUp Node Failed: {str(e)}"}