"""
Roblox Node - Studio Standard
Batch 76: Gaming & Meta
"""
from typing import Any, Dict, Optional, List
import aiohttp
from ..base import BaseNode
from ..registry import register_node

@register_node("roblox_node")
class RobloxNode(BaseNode):
    """
    Manage virtual assets and search experience meta-data via Roblox OpenCloud API.
    """
    node_type = "roblox_node"
    version = "1.0.0"
    category = "gaming"
    credentials_required = ["roblox_auth"]


    properties = [
        {
            'displayName': 'Operation',
            'name': 'operation',
            'type': 'options',
            'default': 'get_universe',
            'options': [
                {'name': 'Get Universe', 'value': 'get_universe'},
                {'name': 'List Assets', 'value': 'list_assets'},
                {'name': 'Get User Info', 'value': 'get_user_info'},
            ],
            'description': 'Roblox action',
        },
        {
            'displayName': 'Universe Id',
            'name': 'universe_id',
            'type': 'string',
            'default': '',
            'description': 'Unique ID of the experience/universe',
        },
        {
            'displayName': 'User Id',
            'name': 'user_id',
            'type': 'string',
            'default': '',
        },
    ]
    inputs = {
        "action": {
            "type": "dropdown",
            "default": "get_universe",
            "options": ["get_universe", "list_assets", "get_user_info"],
            "description": "Roblox action"
        },
        "universe_id": {
            "type": "string",
            "optional": True,
            "description": "Unique ID of the experience/universe"
        },
        "user_id": {
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
            creds = await self.get_credential("roblox_auth")
            api_key = creds.get("api_key") if creds else self.get_config("api_key")
            
            if not api_key:
                return {"status": "error", "error": "Roblox OpenCloud API Key is required."}

            headers = {
                "x-api-key": api_key,
                "Content-Type": "application/json"
            }
            
            base_url = "https://apis.roblox.com"
            action = self.get_config("action", "get_universe")

            async with aiohttp.ClientSession() as session:
                if action == "get_universe":
                    u_id = self.get_config("universe_id") or str(input_data)
                    url = f"{base_url}/universes/v1/universes/{u_id}"
                    async with session.get(url, headers=headers) as resp:
                        res_data = await resp.json()
                        return {"status": "success", "data": {"result": res_data}}

                elif action == "get_user_info":
                    u_id = self.get_config("user_id") or str(input_data)
                    # Note: Using standard public API for user info if OpenCloud lacks it
                    url = f"https://users.roblox.com/v1/users/{u_id}"
                    async with session.get(url) as resp:
                        res_data = await resp.json()
                        return {"status": "success", "data": {"result": res_data}}

                return {"status": "error", "error": f"Unsupported action: {action}"}

        except Exception as e:
            return {"status": "error", "error": f"Roblox Node Failed: {str(e)}"}