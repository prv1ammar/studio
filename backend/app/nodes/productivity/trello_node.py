import aiohttp
from typing import Any, Dict, Optional, List
from ..base import BaseNode
from ..registry import register_node
import json

@register_node("trello_action")
class TrelloNode(BaseNode):
    """
    Automate Trello actions (Cards, Boards).
    """
    node_type = "trello_action"
    version = "1.1.0"
    category = "integrations"
    credentials_required = ["trello_auth"]


    properties = [
        {
            'displayName': 'Operation',
            'name': 'operation',
            'type': 'string',
            'default': 'create_card',
        },
        {
            'displayName': 'Board Id',
            'name': 'board_id',
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
        },
    ]
    inputs = {
        "action": {"type": "string", "default": "create_card", "enum": ["create_card", "get_board_info", "list_cards"]},
        "board_id": {"type": "string", "optional": True},
        "list_id": {"type": "string", "optional": True},
        "name": {"type": "string", "optional": True}
    }
    outputs = {
        "results": {"type": "array"},
        "card_url": {"type": "string"},
        "status": {"type": "string"}
    }

    async def execute(self, input_data: Any, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        try:
            # 1. Resolve Auth
            creds = await self.get_credential("trello_auth")
            key = creds.get("key") or self.get_config("api_key")
            token = creds.get("token") or self.get_config("token")

            if not key or not token:
                return {"status": "error", "error": "Trello API Key and Token are required."}

            action = self.get_config("action", "create_card")
            base_url = "https://api.trello.com/1"
            auth_params = {"key": key, "token": token}

            async with aiohttp.ClientSession() as session:
                if action == "create_card":
                    list_id = self.get_config("list_id")
                    if not list_id:
                        return {"status": "error", "error": "List ID is required for creating cards."}
                    
                    payload = {
                        "idList": list_id,
                        "name": self.get_config("name", "Studio Task"),
                        **auth_params
                    }
                    if isinstance(input_data, str):
                        payload["name"] = input_data
                    elif isinstance(input_data, dict):
                        payload.update(input_data)

                    url = f"{base_url}/cards"
                    async with session.post(url, params=payload) as resp:
                        result = await resp.json()
                        if resp.status >= 400:
                            return {"status": "error", "error": f"Trello Error: {result}"}
                        return {
                            "status": "success",
                            "data": {
                                "id": result.get("id"),
                                "card_url": result.get("shortUrl"),
                                "name": result.get("name")
                            }
                        }

                elif action == "get_board_info":
                    board_id = str(input_data) if isinstance(input_data, str) else self.get_config("board_id")
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
                                "url": result.get("url")
                            }
                        }

                elif action == "list_cards":
                    list_id = self.get_config("list_id")
                    if not list_id:
                        return {"status": "error", "error": "List ID is required to fetch cards."}
                    
                    url = f"{base_url}/lists/{list_id}/cards"
                    async with session.get(url, params=auth_params) as resp:
                        result = await resp.json()
                        if resp.status >= 400:
                            return {"status": "error", "error": f"Trello Error: {result}"}
                        
                        cards = [{"id": c["id"], "name": c["name"], "url": c["shortUrl"]} for c in result]
                        return {
                            "status": "success",
                            "data": {
                                "results": cards,
                                "count": len(cards)
                            }
                        }

            return {"status": "error", "error": f"Unsupported Trello action: {action}"}

        except Exception as e:
            return {"status": "error", "error": f"Trello Node Error: {str(e)}"}