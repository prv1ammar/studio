import aiohttp
import json
from typing import Any, Dict, Optional
from pydantic import Field
from app.nodes.base import BaseNode, NodeConfig
from app.nodes.registry import register_node

class TrelloConfig(NodeConfig):
    api_key: Optional[str] = Field(None, description="Trello API Key")
    token: Optional[str] = Field(None, description="Trello API Token")
    list_id: Optional[str] = Field(None, description="Trello List ID for creating cards")
    credentials_id: Optional[str] = Field(None, description="Trello Credentials ID")
    action: str = Field("create_card", description="Action (create_card, get_board_info)")

@register_node("trello_node")
class TrelloNode(BaseNode):
    node_id = "trello_node"
    config_model = TrelloConfig

    async def execute(self, input_data: Any, context: Optional[Dict[str, Any]] = None) -> Any:
        # 1. Auth Retrieval
        creds = await self.get_credential("credentials_id")
        key = creds.get("key") if creds else self.get_config("api_key")
        token = creds.get("token") if creds else self.get_config("token")
        list_id = self.get_config("list_id")

        if not key or not token:
            return {"error": "Trello API Key and Token are required."}

        action = self.get_config("action")
        base_url = "https://api.trello.com/1"
        
        auth_params = {
            "key": key,
            "token": token
        }

        async with aiohttp.ClientSession() as session:
            try:
                if action == "create_card":
                    if not list_id:
                        return {"error": "List ID is required for creating cards."}
                        
                    url = f"{base_url}/cards"
                    
                    payload = {
                        "idList": list_id,
                        **auth_params
                    }
                    
                    if isinstance(input_data, dict):
                        payload.update(input_data)
                    else:
                        payload["name"] = str(input_data)
                    
                    async with session.post(url, params=payload) as resp:
                        result = await resp.json()
                        if resp.status >= 400:
                            return {"error": f"Trello API Error: {result}"}
                        return {"status": "success", "card_url": result.get("shortUrl"), "id": result.get("id")}

                elif action == "get_board_info":
                    board_id = input_data if isinstance(input_data, str) else None
                    if not board_id:
                         return {"error": "Board ID is required to fetch board info."}
                         
                    url = f"{base_url}/boards/{board_id}"
                    async with session.get(url, params=auth_params) as resp:
                        result = await resp.json()
                        if resp.status >= 400:
                            return {"error": f"Trello API Error: {result}"}
                        return {
                            "name": result.get("name"),
                            "desc": result.get("desc"),
                            "url": result.get("url")
                        }

                return {"error": f"Unsupported Trello action: {action}"}

            except Exception as e:
                return {"error": f"Trello Node Failed: {str(e)}"}
