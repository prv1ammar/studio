"""
Samsara Node - Studio Standard
Batch 80: Industrial & Service Ops
"""
from typing import Any, Dict, Optional, List
import aiohttp
from ..base import BaseNode
from ..registry import register_node

@register_node("samsara_node")
class SamsaraNode(BaseNode):
    """
    Monitor fleet and IoT assets via Samsara API.
    """
    node_type = "samsara_node"
    version = "1.0.0"
    category = "fleet"
    credentials_required = ["samsara_auth"]


    properties = [
        {
            'displayName': 'Operation',
            'name': 'operation',
            'type': 'options',
            'default': 'get_vehicle_locations',
            'options': [
                {'name': 'Get Vehicle Locations', 'value': 'get_vehicle_locations'},
                {'name': 'Get Vehicle Stats', 'value': 'get_vehicle_stats'},
                {'name': 'List Assets', 'value': 'list_assets'},
            ],
            'description': 'Samsara action',
        },
    ]
    inputs = {
        "action": {
            "type": "dropdown",
            "default": "get_vehicle_locations",
            "options": ["get_vehicle_locations", "get_vehicle_stats", "list_assets"],
            "description": "Samsara action"
        }
    }

    outputs = {
        "result": {"type": "any"},
        "status": {"type": "string"}
    }

    async def execute(self, input_data: Any, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        try:
            creds = await self.get_credential("samsara_auth")
            access_token = creds.get("access_token") or creds.get("token")
            
            if not access_token:
                 return {"status": "error", "error": "Samsara Access Token is required."}

            headers = {"Authorization": f"Bearer {access_token}", "Accept": "application/json"}
            base_url = "https://api.samsara.com/v1"
            action = self.get_config("action", "get_vehicle_locations")

            async with aiohttp.ClientSession() as session:
                if action == "get_vehicle_locations":
                    url = f"{base_url}/fleet/locations"
                    async with session.get(url, headers=headers) as resp:
                        res_data = await resp.json()
                        return {"status": "success", "data": {"result": res_data.get("vehicles", [])}}
                
                return {"status": "error", "error": f"Unsupported action: {action}"}
        except Exception as e:
            return {"status": "error", "error": f"Samsara Node Failed: {str(e)}"}