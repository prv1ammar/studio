"""
Hertz Node - Studio Standard (Universal Method)
Batch 88: Automotive & Fleet
"""
from typing import Any, Dict, Optional, List
import aiohttp
from ...base import BaseNode
from ...registry import register_node

@register_node("hertz_node")
class HertzNode(BaseNode):
    """
    Manage Hertz car rental bookings and vehicle availability data.
    """
    node_type = "hertz_node"
    version = "1.0.0"
    category = "automotive"
    credentials_required = ["hertz_auth"]

    inputs = {
        "action": {
            "type": "dropdown",
            "default": "search_vehicles",
            "options": ["search_vehicles", "get_reservation", "create_reservation", "cancel_reservation"],
            "description": "Hertz action"
        },
        "location": {
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
            creds = await self.get_credential("hertz_auth")
            api_key = creds.get("api_key")
            
            if not api_key:
                return {"status": "error", "error": "Hertz API Key required."}

            headers = {
                "X-API-Key": api_key,
                "Content-Type": "application/json"
            }
            
            # 2. Connect to Real API
            base_url = "https://api.hertz.com/v1"
            action = self.get_config("action", "search_vehicles")

            async with aiohttp.ClientSession() as session:
                if action == "search_vehicles":
                    location = self.get_config("location") or str(input_data)
                    url = f"{base_url}/vehicles/search"
                    params = {"location": location}
                    async with session.get(url, headers=headers, params=params) as resp:
                        if resp.status != 200:
                            return {"status": "error", "error": f"Hertz API Error: {resp.status}"}
                        res_data = await resp.json()
                        return {"status": "success", "data": {"result": res_data.get("vehicles", [])}}

                return {"status": "error", "error": f"Unsupported action: {action}"}

        except Exception as e:
            return {"status": "error", "error": f"Hertz Node Failed: {str(e)}"}
