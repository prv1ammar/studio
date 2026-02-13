"""
Fleetio Node - Studio Standard
Batch 80: Industrial & Service Ops
"""
from typing import Any, Dict, Optional, List
import aiohttp
from ...base import BaseNode
from ...registry import register_node

@register_node("fleetio_node")
class FleetioNode(BaseNode):
    """
    Manage vehicle maintenance and fuel via Fleetio API.
    """
    node_type = "fleetio_node"
    version = "1.0.0"
    category = "fleet"
    credentials_required = ["fleetio_auth"]

    inputs = {
        "action": {
            "type": "dropdown",
            "default": "get_vehicles",
            "options": ["get_vehicles", "get_fuel_entries", "get_service_reminders"],
            "description": "Fleetio action"
        }
    }

    outputs = {
        "result": {"type": "any"},
        "status": {"type": "string"}
    }

    async def execute(self, input_data: Any, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        try:
            creds = await self.get_credential("fleetio_auth")
            api_key = creds.get("api_key")
            account_token = creds.get("account_token")
            
            if not api_key or not account_token:
                 return {"status": "error", "error": "Fleetio API Key and Account Token are required."}

            headers = {
                "Authorization": f"Token {api_key}",
                "Account-Token": account_token,
                "Accept": "application/json"
            }
            base_url = "https://secure.fleetio.com/api/v1"
            action = self.get_config("action", "get_vehicles")

            async with aiohttp.ClientSession() as session:
                if action == "get_vehicles":
                    url = f"{base_url}/vehicles"
                    async with session.get(url, headers=headers) as resp:
                        res_data = await resp.json()
                        return {"status": "success", "data": {"result": res_data}}
                
                return {"status": "error", "error": f"Unsupported action: {action}"}
        except Exception as e:
            return {"status": "error", "error": f"Fleetio Node Failed: {str(e)}"}
