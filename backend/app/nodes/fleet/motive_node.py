"""
Motive Node - Studio Standard
Batch 80: Industrial & Service Ops
"""
from typing import Any, Dict, Optional, List
import aiohttp
from ...base import BaseNode
from ...registry import register_node

@register_node("motive_node")
class MotiveNode(BaseNode):
    """
    Track vehicles and safety via Motive (formerly KeepTruckin) API.
    """
    node_type = "motive_node"
    version = "1.0.0"
    category = "fleet"
    credentials_required = ["motive_auth"]

    inputs = {
        "action": {
            "type": "dropdown",
            "default": "get_vehicles",
            "options": ["get_vehicles", "get_driver_logs", "get_safety_scores"],
            "description": "Motive action"
        }
    }

    outputs = {
        "result": {"type": "any"},
        "status": {"type": "string"}
    }

    async def execute(self, input_data: Any, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        try:
            creds = await self.get_credential("motive_auth")
            api_key = creds.get("api_key")
            
            if not api_key:
                 return {"status": "error", "error": "Motive API Key is required."}

            headers = {"X-Api-Key": api_key, "Accept": "application/json"}
            base_url = "https://api.keeptruckin.com/v1"
            action = self.get_config("action", "get_vehicles")

            async with aiohttp.ClientSession() as session:
                if action == "get_vehicles":
                    url = f"{base_url}/vehicles"
                    async with session.get(url, headers=headers) as resp:
                        res_data = await resp.json()
                        return {"status": "success", "data": {"result": res_data.get("vehicles", [])}}
                
                return {"status": "error", "error": f"Unsupported action: {action}"}
        except Exception as e:
            return {"status": "error", "error": f"Motive Node Failed: {str(e)}"}
