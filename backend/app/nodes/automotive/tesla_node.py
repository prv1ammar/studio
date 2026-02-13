"""
Tesla Node - Studio Standard (Universal Method)
Batch 88: Automotive & Fleet
"""
from typing import Any, Dict, Optional, List
import aiohttp
from ...base import BaseNode
from ...registry import register_node

@register_node("tesla_node")
class TeslaNode(BaseNode):
    """
    Orchestrate Tesla vehicle telematics, charging, and state management via Tesla Owner API.
    """
    node_type = "tesla_node"
    version = "1.0.0"
    category = "automotive"
    credentials_required = ["tesla_auth"]

    inputs = {
        "action": {
            "type": "dropdown",
            "default": "list_vehicles",
            "options": ["list_vehicles", "get_vehicle_data", "wake_vehicle", "get_charge_state"],
            "description": "Tesla action"
        },
        "vehicle_id": {
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
            # 1. Authentication (OAuth 2.0)
            creds = await self.get_credential("tesla_auth")
            access_token = creds.get("access_token")
            
            if not access_token:
                return {"status": "error", "error": "Tesla Access Token (OAuth2) required."}

            headers = {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json"
            }
            
            # 2. Connect to Real API
            base_url = "https://owner-api.teslamotors.com/api/1"
            action = self.get_config("action", "list_vehicles")

            async with aiohttp.ClientSession() as session:
                if action == "list_vehicles":
                    url = f"{base_url}/vehicles"
                    async with session.get(url, headers=headers) as resp:
                        if resp.status != 200:
                            return {"status": "error", "error": f"Tesla API Error: {resp.status}"}
                        res_data = await resp.json()
                        return {"status": "success", "data": {"result": res_data.get("response", [])}}

                elif action == "get_vehicle_data":
                    v_id = self.get_config("vehicle_id") or str(input_data)
                    url = f"{base_url}/vehicles/{v_id}/vehicle_data"
                    async with session.get(url, headers=headers) as resp:
                        if resp.status != 200:
                            return {"status": "error", "error": f"Tesla API Error: {resp.status}"}
                        res_data = await resp.json()
                        return {"status": "success", "data": {"result": res_data.get("response", {})}}

                return {"status": "error", "error": f"Unsupported action: {action}"}

        except Exception as e:
            return {"status": "error", "error": f"Tesla Node Failed: {str(e)}"}
