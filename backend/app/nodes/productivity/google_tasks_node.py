"""
Google Tasks Node - Studio Standard
Batch 115: Productivity Suite
"""
from typing import Any, Dict, Optional, List
import aiohttp
from ..base import BaseNode
from ..registry import register_node

@register_node("google_tasks_node")
class GoogleTasksNode(BaseNode):
    """
    Manage Google Tasks (Lists and Tasks).
    """
    node_type = "google_tasks_node"
    version = "1.0.0"
    category = "productivity"
    credentials_required = ["google_tasks_auth"]


    properties = [
        {
            'displayName': 'Operation',
            'name': 'operation',
            'type': 'options',
            'default': 'list_tasks',
            'options': [
                {'name': 'List Tasks', 'value': 'list_tasks'},
                {'name': 'Create Task', 'value': 'create_task'},
                {'name': 'Complete Task', 'value': 'complete_task'},
                {'name': 'List Tasklists', 'value': 'list_tasklists'},
                {'name': 'Create Tasklist', 'value': 'create_tasklist'},
            ],
            'description': 'Google Tasks action',
        },
        {
            'displayName': 'Due',
            'name': 'due',
            'type': 'string',
            'default': '',
            'description': 'RFC 3339 timestamp (e.g., 2024-12-31T23:59:59.000Z)',
        },
        {
            'displayName': 'Notes',
            'name': 'notes',
            'type': 'string',
            'default': '',
            'description': 'Task notes/description',
        },
        {
            'displayName': 'Task Id',
            'name': 'task_id',
            'type': 'string',
            'default': '',
        },
        {
            'displayName': 'Tasklist Id',
            'name': 'tasklist_id',
            'type': 'string',
            'default': '@default',
            'description': 'Tasklist ID (use @default for the primary list)',
        },
        {
            'displayName': 'Title',
            'name': 'title',
            'type': 'string',
            'default': '',
            'description': 'Task title',
        },
    ]
    inputs = {
        "action": {
            "type": "dropdown",
            "default": "list_tasks",
            "options": ["list_tasks", "create_task", "complete_task", "list_tasklists", "create_tasklist"],
            "description": "Google Tasks action"
        },
        "tasklist_id": {
            "type": "string",
            "default": "@default",
            "description": "Tasklist ID (use @default for the primary list)"
        },
        "task_id": {
            "type": "string",
            "optional": True
        },
        "title": {
            "type": "string",
            "optional": True,
            "description": "Task title"
        },
        "notes": {
            "type": "string",
            "optional": True,
            "description": "Task notes/description"
        },
        "due": {
            "type": "string",
            "optional": True,
            "description": "RFC 3339 timestamp (e.g., 2024-12-31T23:59:59.000Z)"
        }
    }

    outputs = {
        "result": {"type": "any"},
        "status": {"type": "string"}
    }

    async def execute(self, input_data: Any, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        try:
            creds = await self.get_credential("google_tasks_auth")
            access_token = creds.get("access_token")
            
            if not access_token:
                return {"status": "error", "error": "Google Tasks access token required"}

            base_url = "https://tasks.googleapis.com/tasks/v1"
            headers = {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json"
            }
            
            action = self.get_config("action", "list_tasks")
            tasklist_id = self.get_config("tasklist_id", "@default")

            async with aiohttp.ClientSession() as session:
                if action == "list_tasks":
                    url = f"{base_url}/lists/{tasklist_id}/tasks"
                    async with session.get(url, headers=headers) as resp:
                        res_data = await resp.json()
                        if resp.status != 200:
                            return {"status": "error", "error": f"Google Tasks Error: {res_data.get('error', {}).get('message', 'Unknown')}"}
                        return {"status": "success", "data": {"result": res_data.get("items", [])}}

                elif action == "create_task":
                    title = self.get_config("title") or str(input_data)
                    notes = self.get_config("notes", "")
                    due = self.get_config("due")
                    
                    if not title:
                        return {"status": "error", "error": "title required"}
                    
                    payload = {"title": title, "notes": notes}
                    if due: payload["due"] = due
                    
                    url = f"{base_url}/lists/{tasklist_id}/tasks"
                    async with session.post(url, headers=headers, json=payload) as resp:
                        res_data = await resp.json()
                        if resp.status != 200:
                             return {"status": "error", "error": f"Google Tasks Error: {res_data.get('error', {}).get('message', 'Unknown')}"}
                        return {"status": "success", "data": {"result": res_data}}

                elif action == "complete_task":
                    task_id = self.get_config("task_id") or str(input_data)
                    if not task_id:
                        return {"status": "error", "error": "task_id required"}
                    
                    url = f"{base_url}/lists/{tasklist_id}/tasks/{task_id}"
                    async with session.patch(url, headers=headers, json={"status": "completed"}) as resp:
                        res_data = await resp.json()
                        if resp.status != 200:
                             return {"status": "error", "error": f"Google Tasks Error: {res_data.get('error', {}).get('message', 'Unknown')}"}
                        return {"status": "success", "data": {"result": res_data}}

                elif action == "list_tasklists":
                    url = f"{base_url}/users/@me/lists"
                    async with session.get(url, headers=headers) as resp:
                        res_data = await resp.json()
                        return {"status": "success", "data": {"result": res_data.get("items", [])}}

            return {"status": "error", "error": f"Unsupported action: {action}"}

        except Exception as e:
            return {"status": "error", "error": f"Google Tasks Node Failed: {str(e)}"}