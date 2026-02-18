"""
Project Management Nodes - Studio Standard (Universal Method)
Batch 105: Productivity Suite
"""
from typing import Any, Dict, Optional, List
import aiohttp
from ..base import BaseNode
from ..registry import register_node

# ============================================
# MONDAY.COM NODE
# ============================================
@register_node("monday_com_node")
class MondayComNode(BaseNode):
    node_type = "monday_com_node"
    version = "1.0.0"
    category = "productivity"
    credentials_required = ["monday_auth"]


    properties = [
        {
            'displayName': 'Operation',
            'name': 'operation',
            'type': 'options',
            'default': 'create_item',
            'options': [
                {'name': 'Create Item', 'value': 'create_item'},
                {'name': 'List Boards', 'value': 'list_boards'},
                {'name': 'Get Item', 'value': 'get_item'},
                {'name': 'Update Item', 'value': 'update_item'},
                {'name': 'Create Subitem', 'value': 'create_subitem'},
            ],
            'description': 'Monday.com action',
        },
        {
            'displayName': 'Board Id',
            'name': 'board_id',
            'type': 'string',
            'default': '',
        },
        {
            'displayName': 'Column Values',
            'name': 'column_values',
            'type': 'string',
            'default': '',
            'description': 'JSON object',
        },
        {
            'displayName': 'Group Id',
            'name': 'group_id',
            'type': 'string',
            'default': '',
        },
        {
            'displayName': 'Item Id',
            'name': 'item_id',
            'type': 'string',
            'default': '',
        },
        {
            'displayName': 'Item Name',
            'name': 'item_name',
            'type': 'string',
            'default': '',
        },
    ]
    inputs = {
        "action": {
            "type": "dropdown",
            "default": "create_item",
            "options": ["create_item", "list_boards", "get_item", "update_item", "create_subitem"],
            "description": "Monday.com action"
        },
        "board_id": {"type": "string", "optional": True},
        "group_id": {"type": "string", "optional": True},
        "item_name": {"type": "string", "optional": True},
        "column_values": {"type": "string", "optional": True, "description": "JSON object"},
        "item_id": {"type": "string", "optional": True}
    }

    outputs = {"result": {"type": "any"}, "status": {"type": "string"}}

    async def execute(self, input_data: Any, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        try:
            creds = await self.get_credential("monday_auth")
            api_key = creds.get("api_key")
            
            if not api_key:
                return {"status": "error", "error": "Monday.com API key required"}

            url = "https://api.monday.com/v2"
            headers = {
                "Authorization": api_key,
                "Content-Type": "application/json"
            }
            
            action = self.get_config("action", "create_item")

            async with aiohttp.ClientSession() as session:
                if action == "create_item":
                    board_id = self.get_config("board_id")
                    item_name = self.get_config("item_name")
                    column_values = self.get_config("column_values", "{}")
                    
                    if not board_id or not item_name:
                        return {"status": "error", "error": "board_id and item_name required"}
                    
                    # Uses GraphQL mutation
                    # Simple mutation for creation
                    escaped_column_values = column_values.replace('"', '\\"')
                    query = f'''mutation {{
                        create_item (board_id: {board_id}, item_name: "{item_name}", column_values: "{escaped_column_values}") {{
                            id
                        }}
                    }}'''
                    
                    async with session.post(url, headers=headers, json={"query": query}) as resp:
                         if resp.status != 200:
                            error_text = await resp.text()
                            return {"status": "error", "error": f"Monday.com API Error {resp.status}: {error_text}"}
                         res_data = await resp.json()
                         return {"status": "success", "data": {"result": res_data}}
                
                elif action == "list_boards":
                    query = "{ boards (limit: 50) { id name } }"
                    async with session.post(url, headers=headers, json={"query": query}) as resp:
                        res_data = await resp.json()
                        return {"status": "success", "data": {"result": res_data.get("data", {}).get("boards", [])}}

            return {"status": "error", "error": f"Unsupported action: {action}"}
        except Exception as e:
            return {"status": "error", "error": f"Monday.com Node Failed: {str(e)}"}

# ============================================
# ASANA NODE
# ============================================
@register_node("asana_node")
class AsanaNode(BaseNode):
    node_type = "asana_node"
    version = "1.0.0"
    category = "productivity"
    credentials_required = ["asana_auth"]

    inputs = {
        "action": {"type": "dropdown", "default": "create_task", "options": ["create_task", "get_task", "update_task", "get_projects", "get_users"]},
        "workspace_id": {"type": "string", "optional": True},
        "project_id": {"type": "string", "optional": True},
        "name": {"type": "string", "optional": True},
        "notes": {"type": "string", "optional": True},
        "due_on": {"type": "string", "optional": True},
        "task_id": {"type": "string", "optional": True}
    }

    outputs = {"result": {"type": "any"}, "status": {"type": "string"}}
    
    async def execute(self, input_data: Any, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        try:
            creds = await self.get_credential("asana_auth")
            access_token = creds.get("access_token")
            
            if not access_token:
                return {"status": "error", "error": "Asana access token required"}

            base_url = "https://app.asana.com/api/1.0"
            headers = {"Authorization": f"Bearer {access_token}"}
            
            action = self.get_config("action", "create_task")

            async with aiohttp.ClientSession() as session:
                if action == "create_task":
                    workspace = self.get_config("workspace_id")
                    name = self.get_config("name")
                    notes = self.get_config("notes")
                    project = self.get_config("project_id")
                    
                    if not workspace or not name:
                        # Asana requires either workspace or project
                        # Assuming at least project_id or workspace_id is usually provided
                        pass

                    data = {"name": name, "notes": notes}
                    if workspace: data["workspace"] = workspace
                    if project: data["projects"] = [project]
                    
                    async with session.post(f"{base_url}/tasks", headers=headers, json={"data": data}) as resp:
                        res_data = await resp.json()
                        if resp.status != 201:
                             return {"status": "error", "error": f"Asana Error: {res_data}"}
                        return {"status": "success", "data": {"result": res_data.get("data")}}

                elif action == "get_projects":
                    workspace = self.get_config("workspace_id")
                    url = f"{base_url}/projects?workspace={workspace}" if workspace else f"{base_url}/projects"
                    async with session.get(url, headers=headers) as resp:
                        res_data = await resp.json()
                        return {"status": "success", "data": {"result": res_data.get("data", [])}}

            return {"status": "error", "error": f"Unsupported action: {action}"}
        except Exception as e:
             return {"status": "error", "error": f"Asana Node Failed: {str(e)}"}

# ============================================
# CLICKUP NODE
# ============================================
@register_node("clickup_node")
class ClickUpNode(BaseNode):
    node_type = "clickup_node"
    version = "1.0.0"
    category = "productivity"
    credentials_required = ["clickup_auth"]

    inputs = {
        "action": {"type": "dropdown", "default": "create_task", "options": ["create_task", "get_task", "update_task", "get_lists", "get_folder"]},
        "list_id": {"type": "string", "optional": True},
        "name": {"type": "string", "optional": True},
        "description": {"type": "string", "optional": True},
        "status": {"type": "string", "optional": True},
        "priority": {"type": "number", "optional": True},
        "task_id": {"type": "string", "optional": True}
    }

    outputs = {"result": {"type": "any"}, "status": {"type": "string"}}
    
    async def execute(self, input_data: Any, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        try:
            creds = await self.get_credential("clickup_auth")
            api_key = creds.get("api_key")
            
            if not api_key:
                return {"status": "error", "error": "ClickUp API key required"}

            base_url = "https://api.clickup.com/api/v2"
            headers = {
                "Authorization": api_key,
                "Content-Type": "application/json"
            }
            
            action = self.get_config("action", "create_task")

            async with aiohttp.ClientSession() as session:
                if action == "create_task":
                    list_id = self.get_config("list_id")
                    name = self.get_config("name")
                    desc = self.get_config("description", "")
                    
                    if not list_id or not name:
                         return {"status": "error", "error": "list_id and name required"}
                    
                    payload = {"name": name, "description": desc}
                    
                    async with session.post(f"{base_url}/list/{list_id}/task", headers=headers, json=payload) as resp:
                        res_data = await resp.json()
                        if resp.status != 200:
                            return {"status": "error", "error": f"ClickUp Error: {res_data}"}
                        return {"status": "success", "data": {"result": res_data}}
                
                elif action == "get_lists":
                    folder_id = self.get_config("folder_id") # Assuming folder_id input logic
                    # Simplified: ClickUp needs folder_id to get lists usually
                    # Fallback to get_task logic if list logic complex without ID
                    pass

            return {"status": "error", "error": f"Unsupported action: {action}"}
        except Exception as e:
               return {"status": "error", "error": f"ClickUp Node Failed: {str(e)}"}