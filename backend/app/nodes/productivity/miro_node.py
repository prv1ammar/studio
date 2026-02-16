"""
Miro Node - Studio Standard
Batch 113: Productivity & Collaboration
"""
from typing import Any, Dict, Optional
import aiohttp
from ...base import BaseNode
from ...registry import register_node

@register_node("miro_node")
class MiroNode(BaseNode):
    """
    Interact with Miro boards and items.
    """
    node_type = "miro_node"
    version = "1.0.0"
    category = "productivity"
    credentials_required = ["miro_auth"]

    inputs = {
        "action": {
            "type": "dropdown",
            "default": "list_boards",
            "options": ["list_boards", "get_board", "create_board", "list_items", "create_sticky_note"],
            "description": "Miro action"
        },
        "board_id": {
            "type": "string",
            "optional": True,
            "description": "Miro Board ID"
        },
        "content": {
            "type": "string",
            "optional": True,
            "description": "Content for sticky note"
        }
    }

    outputs = {
        "result": {"type": "any"},
        "status": {"type": "string"}
    }

    async def execute(self, input_data: Any, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        try:
            creds = await self.get_credential("miro_auth")
            api_token = creds.get("access_token") or creds.get("token")
            
            if not api_token:
                return {"status": "error", "error": "Miro Access Token required"}

            headers = {
                "Authorization": f"Bearer {api_token}",
                "Content-Type": "application/json"
            }
            
            action = self.get_config("action", "list_boards")
            base_url = "https://api.miro.com/v2"

            async with aiohttp.ClientSession() as session:
                if action == "list_boards":
                    url = f"{base_url}/boards"
                    async with session.get(url, headers=headers) as resp:
                        res_data = await resp.json()
                        return {"status": "success", "data": {"result": res_data.get("data", [])}}

                elif action == "get_board":
                    board_id = self.get_config("board_id") or str(input_data)
                    url = f"{base_url}/boards/{board_id}"
                    async with session.get(url, headers=headers) as resp:
                        res_data = await resp.json()
                        return {"status": "success", "data": {"result": res_data}}

                elif action == "create_board":
                    name = self.get_config("content") or "New Board"
                    url = f"{base_url}/boards"
                    payload = {"name": name, "policy": {"permissionsPolicy": {"collaborationToolsStartMindmap": "all_editors"}}}
                    async with session.post(url, headers=headers, json=payload) as resp:
                        res_data = await resp.json()
                        return {"status": "success", "data": {"result": res_data}}

                elif action == "create_sticky_note":
                    board_id = self.get_config("board_id")
                    content = self.get_config("content") or str(input_data)
                    if not board_id: return {"status": "error", "error": "board_id required"}
                    
                    url = f"{base_url}/boards/{board_id}/sticky_notes"
                    payload = {
                        "data": {"content": content},
                        "position": {"x": 0, "y": 0}
                    }
                    async with session.post(url, headers=headers, json=payload) as resp:
                        if resp.status >= 400:
                            return {"status": "error", "error": f"Miro Error: {await resp.text()}"}
                        res_data = await resp.json()
                        return {"status": "success", "data": {"result": res_data}}

            return {"status": "error", "error": f"Unsupported action: {action}"}

        except Exception as e:
            return {"status": "error", "error": f"Miro Node Failed: {str(e)}"}
