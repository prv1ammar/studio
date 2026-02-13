"""
Ford Node - Studio Standard (Universal Method)
Batch 88: Automotive & Fleet
"""
from typing import Any, Dict, Optional, List
import aiohttp
from ...base import BaseNode
from ...registry import register_node

@register_node("ford_node")
class FordNode(BaseNode):
    """
    Access Ford vehicle status and health reports via FordPass/Pro APIs.
    """
    node_type = "ford_node"
    version = "1.0.0"
    category = "automotive"
    credentials_required = ["ford_auth"]

    inputs = {
        "action": {
            "type": "dropdown",
            "default": "get_vehicle_status",
            "options": ["get_vehicle_status", "get_vehicle_location", "lock_vehicle", "unlock_vehicle"],
            "description": "Ford action"
        },
        "vin": {
            "type": "string",
            "required": True,
            "description": "Vehicle Identification Number"
        }
    }

    outputs = {
        "result": {"type": "any"},
        "status": {"type": "string"}
    }

    async def execute(self, input_data: Any, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        try:
            # 1. Authentication
            creds = await self.get_credential("ford_auth")
            access_token = creds.get("access_token")
            
            if not access_token:
                return {"status": "error", "error": "Ford Access Token required."}

            headers = {
                "Authorization": f"Bearer {access_token}",
                "Application-Id": creds.get("application_id", ""),
                "Content-Type": "application/json"
            }
            
            # 2. Connect to Real API
            base_url = "https://api.mps.ford.com/api"
            action = self.get_config("action", "get_vehicle_status")
            vin = self.get_config("vin")

            async with aiohttp.ClientSession() as session:
                if action == "get_vehicle_status":
                    url = f"{base_url}/vehicles/v4/{vin}/status"
                    async with session.get(url, headers=headers) as resp:
                        if resp.status != 200:
                            return {"status": "error", "error": f"Ford API Error: {resp.status}"}
                        res_data = await resp.json()
                        return {"status": "success", "data": {"result": res_data.get("vehiclestatus", {})}}

                elif action == "get_vehicle_location":
                    url = f"{base_url}/vehicles/v2/{vin}/location"
                    async with session.get(url, headers=headers) as resp:
                        if resp.status != 200:
                            return {"status": "error", "error": f"Ford API Error: {resp.status}"}
                        res_data = await resp.json()
                        return {"status": "success", "data": {"result": res_data}}

                return {"status": "error", "error": f"Unsupported action: {action}"}

        except Exception as e:
            return {"status": "error", "error": f"Ford Node Failed: {str(e)}"}
