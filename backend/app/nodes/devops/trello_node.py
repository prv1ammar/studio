"""
Trello Ops Node - Studio Standard
Batch 47: Developer Tools & Ops
"""
from typing import Any, Dict, Optional, List
import aiohttp
import json
from ...base import BaseNode
from ...registry import register_node

@register_node("trello_node")
class TrelloNode(BaseNode):
    """
    Manage Trello boards and cards.
    Supports: Create Card, Get Board, List Cards, Add Comment.
    """
    node_type = "trello_node"
    version = "1.0.0"
    category = "devops"
    credentials_required = ["trello_auth"]

    inputs = {
        "action": {
            "type": "dropdown",
            "default": "create_card",
            "options": ["create_card", "get_board", "list_cards", "add_comment"],
            "description": "Trello action to perform"
        },
        "board_id": {
            "type": "string",
            "optional": True,
            "description": "ID of the Trello board"
        },
        "list_id": {
            "type": "string",
            "optional": True,
            "description": "ID of the Trello list"
        },
        "card_id": {
            "type": "string",
            "optional": True,
            "description": "ID of a specific card"
        },
        "payload": {
            "type": "json",
            "optional": True,
            "description": "Structured data (name, description, etc.)"
        }
    }

    outputs = {
        "id": {"type": "string"},
        "url": {"type": "string"},
        "result": {"type": "any"}
    }

    async def execute(self, input_data: Any, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        try:
            # 1. Resolve Auth
            creds = await self.get_credential("trello_auth")
            key = None
            token = None
            
            if creds:
                key = creds.get("key") or creds.get("api_key")
                token = creds.get("token")
            
            if not key or not token:
                key = self.get_config("api_key")
                token = self.get_config("token")

            if not key or not token:
                return {"status": "error", "error": "Trello API Key and Token are required."}

            action = self.get_config("action", "create_card")
            base_url = "https://api.trello.com/1"
            auth_params = {"key": key, "token": token}

            async with aiohttp.ClientSession() as session:
                if action == "create_card":
                    list_id = self.get_config("list_id")
                    if not list_id:
                         return {"status": "error", "error": "List ID is required to create a card."}
                    
                    data = self.get_config("payload", {})
                    if isinstance(input_data, dict):
                        data.update(input_data)
                    
                    name = data.get("name") or (input_data if isinstance(input_data, str) else "Studio Task")
                    desc = data.get("desc") or data.get("description", "")
                    
                    payload = {
                        "idList": list_id,
                        "name": name,
                        "desc": desc,
                        **auth_params
                    }
                    
                    url = f"{base_url}/cards"
                    async with session.post(url, params=payload) as resp:
                        result = await resp.json()
                        if resp.status >= 400:
                            return {"status": "error", "error": f"Trello API Error: {result}"}
                        
                        return {
                            "status": "success",
                            "data": {
                                "id": result.get("id"),
                                "url": result.get("shortUrl"),
                                "result": result
                            }
                        }

                elif action == "get_board":
                    board_id = self.get_config("board_id") or (input_data if isinstance(input_data, str) else None)
                    if not board_id:
                         return {"status": "error", "error": "Board ID is required."}
                    
                    url = f"{base_url}/boards/{board_id}"
                    async with session.get(url, params=auth_params) as resp:
                        result = await resp.json()
                        if resp.status >= 400:
                             return {"status": "error", "error": f"Trello Error: {result}"}
                        return {
                            "status": "success",
                            "data": {
                                "id": result.get("id"),
                                "name": result.get("name"),
                                "url": result.get("url"),
                                "result": result
                            }
                        }

                elif action == "list_cards":
                    list_id = self.get_config("list_id") or (input_data if isinstance(input_data, str) else None)
                    if not list_id:
                         return {"status": "error", "error": "List ID is required."}
                    
                    url = f"{base_url}/lists/{list_id}/cards"
                    async with session.get(url, params=auth_params) as resp:
                        result = await resp.json()
                        if resp.status >= 400:
                             return {"status": "error", "error": f"Trello Error: {result}"}
                        return {
                            "status": "success",
                            "data": {
                                "result": result,
                                "count": len(result)
                            }
                        }

                elif action == "add_comment":
                    card_id = self.get_config("card_id") or (input_data if isinstance(input_data, str) and len(input_data) > 10 else None)
                    text = self.get_config("payload", {}).get("text") or (input_data if isinstance(input_data, str) and len(input_data) <= 10 or " " in input_data else None)
                    
                    if not card_id or not text:
                         return {"status": "error", "error": "Card ID and comment text are required."}
                    
                    url = f"{base_url}/cards/{card_id}/actions/comments"
                    params = {"text": text, **auth_params}
                    async with session.post(url, params=params) as resp:
                        result = await resp.json()
                        if resp.status >= 400:
                             return {"status": "error", "error": f"Trello Error: {result}"}
                        return {
                            "status": "success",
                            "data": {
                                "id": result.get("id"),
                                "result": result
                            }
                        }

                return {"status": "error", "error": f"Unsupported action: {action}"}

        except Exception as e:
            return {"status": "error", "error": f"Trello Node Failed: {str(e)}"}
