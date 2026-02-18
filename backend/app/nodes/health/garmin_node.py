"""
Garmin Node - Studio Standard
Batch 81: Leisure, Health & Education
"""
from typing import Any, Dict, Optional, List
import aiohttp
from ..base import BaseNode
from ..registry import register_node

@register_node("garmin_node")
class GarminNode(BaseNode):
    """
    Retrieve biometric and wellness data via Garmin Health API.
    """
    node_type = "garmin_node"
    version = "1.0.0"
    category = "health"
    credentials_required = ["garmin_auth"]


    properties = [
        {
            'displayName': 'Operation',
            'name': 'operation',
            'type': 'options',
            'default': 'get_daily_summary',
            'options': [
                {'name': 'Get Daily Summary', 'value': 'get_daily_summary'},
                {'name': 'Get Sleep Data', 'value': 'get_sleep_data'},
                {'name': 'Get Activity Data', 'value': 'get_activity_data'},
            ],
            'description': 'Garmin action',
        },
    ]
    inputs = {
        "action": {
            "type": "dropdown",
            "default": "get_daily_summary",
            "options": ["get_daily_summary", "get_sleep_data", "get_activity_data"],
            "description": "Garmin action"
        }
    }

    outputs = {
        "result": {"type": "any"},
        "status": {"type": "string"}
    }

    async def execute(self, input_data: Any, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        try:
            creds = await self.get_credential("garmin_auth")
            # Garmin Health usually uses OAuth 2.0 now
            access_token = creds.get("access_token")
            
            if not access_token:
                return {"status": "error", "error": "Garmin Access Token required."}

            headers = {"Authorization": f"Bearer {access_token}", "Accept": "application/json"}
            base_url = "https://healthapi.garmin.com/wellness-api/rest"
            action = self.get_config("action", "get_daily_summary")

            async with aiohttp.ClientSession() as session:
                if action == "get_daily_summary":
                    url = f"{base_url}/dailies"
                    async with session.get(url, headers=headers) as resp:
                        res_data = await resp.json()
                        return {"status": "success", "data": {"result": res_data}}
                
                return {"status": "error", "error": f"Unsupported action: {action}"}
        except Exception as e:
            return {"status": "error", "error": f"Garmin Node Failed: {str(e)}"}