"""
Avis Node - Studio Standard (Universal Method)
Batch 88: Automotive & Fleet
"""
from typing import Any, Dict, Optional, List
import aiohttp
from ...base import BaseNode
from ...registry import register_node

@register_node("avis_node")
class AvisNode(BaseNode):
    """
    Orchestrate Avis rental logistics and fleet status.
    """
    node_type = "avis_node"
    version = "1.0.0"
    category = "automotive"
    credentials_required = ["avis_auth"]

    inputs = {
        "action": {
            "type": "dropdown",
            "default": "search_rentals",
            "options": ["search_rentals", "get_reservation_details", "modify_reservation"],
            "description": "Avis action"
        },
        "pickup_location": {
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
            creds = await self.get_credential("avis_auth")
            api_key = creds.get("api_key")
            
            if not api_key:
                return {"status": "error", "error": "Avis API Key required."}

            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            }
            
            # 2. Connect to Real API
            base_url = "https://stage.abgapiservices.com:443/cars/catalog/v1"
            action = self.get_config("action", "search_rentals")

            async with aiohttp.ClientSession() as session:
                if action == "search_rentals":
                    pickup = self.get_config("pickup_location") or str(input_data)
                    url = f"{base_url}/vehicles"
                    params = {"brand": "Avis", "pickUpLocation": pickup}
                    async with session.get(url, headers=headers, params=params) as resp:
                        if resp.status != 200:
                            return {"status": "error", "error": f"Avis API Error: {resp.status}"}
                        res_data = await resp.json()
                        return {"status": "success", "data": {"result": res_data.get("vehicles", [])}}

                return {"status": "error", "error": f"Unsupported action: {action}"}

        except Exception as e:
            return {"status": "error", "error": f"Avis Node Failed: {str(e)}"}
