"""
Monday.com Node - Studio Standard (Universal Method)
Batch 90: CRM & Marketing (n8n Critical)
"""
from typing import Any, Dict, Optional, List
import aiohttp
from ...base import BaseNode
from ...registry import register_node

@register_node("monday_node")
class MondayNode(BaseNode):
    """
    Manage boards, items, and updates in Monday.com via GraphQL API.
    """
    node_type = "monday_node"
    version = "1.0.0"
    category = "collaboration"
    credentials_required = ["monday_auth"]

    inputs = {
        "action": {
            "type": "dropdown",
            "default": "create_item",
            "options": ["create_item", "get_boards", "get_items", "update_item", "create_update"],
            "description": "Monday.com action"
        },
        "board_id": {
            "type": "string",
            "optional": True
        },
        "item_name": {
            "type": "string",
            "optional": True
        }
    }

    outputs = {
        "result": {"type": "any"},
        "status": {"type": "string"}
    }

    async def execute(self, input_data: Any, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        try:
            # 1. Authentication
            creds = await self.get_credential("monday_auth")
            api_token = creds.get("api_token")
            
            if not api_token:
                return {"status": "error", "error": "Monday.com API Token required."}

            headers = {
                "Authorization": api_token,
                "Content-Type": "application/json",
                "API-Version": "2024-01"
            }
            
            # 2. Connect to Real API (GraphQL)
            url = "https://api.monday.com/v2"
            action = self.get_config("action", "create_item")

            async with aiohttp.ClientSession() as session:
                if action == "create_item":
                    board_id = self.get_config("board_id")
                    item_name = self.get_config("item_name") or str(input_data)
                    
                    if not board_id:
                        return {"status": "error", "error": "board_id required"}
                    
                    query = f'''
                        mutation {{
                            create_item (board_id: {board_id}, item_name: "{item_name}") {{
                                id
                                name
                            }}
                        }}
                    '''
                    async with session.post(url, headers=headers, json={"query": query}) as resp:
                        if resp.status != 200:
                            return {"status": "error", "error": f"Monday.com Error: {resp.status}"}
                        res_data = await resp.json()
                        return {"status": "success", "data": {"result": res_data.get("data", {}).get("create_item", {})}}

                elif action == "get_boards":
                    query = '''
                        query {
                            boards (limit: 50) {
                                id
                                name
                                description
                            }
                        }
                    '''
                    async with session.post(url, headers=headers, json={"query": query}) as resp:
                        if resp.status != 200:
                            return {"status": "error", "error": f"Monday.com Error: {resp.status}"}
                        res_data = await resp.json()
                        return {"status": "success", "data": {"result": res_data.get("data", {}).get("boards", [])}}

                elif action == "get_items":
                    board_id = self.get_config("board_id")
                    if not board_id:
                        return {"status": "error", "error": "board_id required"}
                    
                    query = f'''
                        query {{
                            boards (ids: {board_id}) {{
                                items {{
                                    id
                                    name
                                    state
                                }}
                            }}
                        }}
                    '''
                    async with session.post(url, headers=headers, json={"query": query}) as resp:
                        if resp.status != 200:
                            return {"status": "error", "error": f"Monday.com Error: {resp.status}"}
                        res_data = await resp.json()
                        boards = res_data.get("data", {}).get("boards", [])
                        items = boards[0].get("items", []) if boards else []
                        return {"status": "success", "data": {"result": items}}

                return {"status": "error", "error": f"Unsupported action: {action}"}

        except Exception as e:
            return {"status": "error", "error": f"Monday.com Node Failed: {str(e)}"}
