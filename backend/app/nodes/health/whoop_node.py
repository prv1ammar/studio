"""
Whoop Node - Studio Standard
Batch 81: Leisure, Health & Education
"""
from typing import Any, Dict, Optional, List
import aiohttp
from ...base import BaseNode
from ...registry import register_node

@register_node("whoop_node")
class WhoopNode(BaseNode):
    """
    Retrieve strain, recovery, and sleep data via Whoop API.
    """
    node_type = "whoop_node"
    version = "1.0.0"
    category = "health"
    credentials_required = ["whoop_auth"]

    inputs = {
        "action": {
            "type": "dropdown",
            "default": "get_recovery_data",
            "options": ["get_recovery_data", "get_sleep_data", "get_cycle_data", "get_profile"],
            "description": "Whoop action"
        }
    }

    outputs = {
        "result": {"type": "any"},
        "status": {"type": "string"}
    }

    async def execute(self, input_data: Any, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        try:
            creds = await self.get_credential("whoop_auth")
            access_token = creds.get("access_token")
            
            if not access_token:
                return {"status": "error", "error": "Whoop Access Token required."}

            headers = {"Authorization": f"Bearer {access_token}", "Accept": "application/json"}
            base_url = "https://api.prod.whoop.com/developer/v1"
            action = self.get_config("action", "get_recovery_data")

            async with aiohttp.ClientSession() as session:
                if action == "get_recovery_data":
                    url = f"{base_url}/recovery"
                    async with session.get(url, headers=headers) as resp:
                        res_data = await resp.json()
                        return {"status": "success", "data": {"result": res_data}}
                
                elif action == "get_profile":
                    url = f"{base_url}/user/profile/basic"
                    async with session.get(url, headers=headers) as resp:
                        res_data = await resp.json()
                        return {"status": "success", "data": {"result": res_data}}

                return {"status": "error", "error": f"Unsupported action: {action}"}
        except Exception as e:
            return {"status": "error", "error": f"Whoop Node Failed: {str(e)}"}
