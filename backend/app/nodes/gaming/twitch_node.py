"""
Twitch Node - Studio Standard
Batch 76: Gaming & Meta
"""
from typing import Any, Dict, Optional, List
import aiohttp
from ...base import BaseNode
from ...registry import register_node

@register_node("twitch_node")
class TwitchNode(BaseNode):
    """
    Automate stream monitoring and channel discovery via the Twitch Helix API.
    """
    node_type = "twitch_node"
    version = "1.0.0"
    category = "gaming"
    credentials_required = ["twitch_auth"]

    inputs = {
        "action": {
            "type": "dropdown",
            "default": "get_streams",
            "options": ["get_streams", "get_channel_info", "get_clips", "search_channels"],
            "description": "Twitch action"
        },
        "query": {
            "type": "string",
            "optional": True,
            "description": "Search query or channel name"
        },
        "broadcaster_id": {
            "type": "string",
            "optional": True,
            "description": "Unique ID of the broadcaster"
        }
    }

    outputs = {
        "result": {"type": "any"},
        "status": {"type": "string"},
        "count": {"type": "number"}
    }

    async def execute(self, input_data: Any, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        try:
            creds = await self.get_credential("twitch_auth")
            client_id = creds.get("client_id") if creds else self.get_config("client_id")
            client_secret = creds.get("client_secret") if creds else self.get_config("client_secret")
            
            if not client_id or not client_secret:
                return {"status": "error", "error": "Twitch Client ID and Secret are required."}

            async with aiohttp.ClientSession() as session:
                # 1. Get Access Token (Client Credentials Flow)
                auth_url = "https://id.twitch.tv/oauth2/token"
                auth_params = {
                    "client_id": client_id,
                    "client_secret": client_secret,
                    "grant_type": "client_credentials"
                }
                async with session.post(auth_url, params=auth_params) as auth_resp:
                    auth_json = await auth_resp.json()
                    access_token = auth_json.get("access_token")

                if not access_token:
                    return {"status": "error", "error": f"Failed to get Twitch access token: {auth_json}"}

                headers = {
                    "Client-ID": client_id,
                    "Authorization": f"Bearer {access_token}"
                }
                
                base_url = "https://api.twitch.tv/helix"
                action = self.get_config("action", "get_streams")

                if action == "get_streams":
                    user_login = self.get_config("query") or str(input_data)
                    url = f"{base_url}/streams"
                    params = {"user_login": user_login} if user_login else {}
                    async with session.get(url, headers=headers, params=params) as resp:
                        res_data = await resp.json()
                        data = res_data.get("data", [])
                        return {"status": "success", "data": {"result": data, "count": len(data)}}

                elif action == "get_channel_info":
                    b_id = self.get_config("broadcaster_id") or str(input_data)
                    if not b_id:
                        return {"status": "error", "error": "broadcaster_id is required."}
                    url = f"{base_url}/channels"
                    params = {"broadcaster_id": b_id}
                    async with session.get(url, headers=headers, params=params) as resp:
                        res_data = await resp.json()
                        data = res_data.get("data", [])
                        return {"status": "success", "data": {"result": data[0] if data else {}}}

                elif action == "search_channels":
                    query = self.get_config("query") or str(input_data)
                    url = f"{base_url}/search/channels"
                    params = {"query": query}
                    async with session.get(url, headers=headers, params=params) as resp:
                        res_data = await resp.json()
                        data = res_data.get("data", [])
                        return {"status": "success", "data": {"result": data, "count": len(data)}}

                return {"status": "error", "error": f"Unsupported action: {action}"}

        except Exception as e:
            return {"status": "error", "error": f"Twitch Node Failed: {str(e)}"}
