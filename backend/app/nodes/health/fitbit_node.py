"""
Fitbit Node - Studio Standard
Batch 77: Health & Fitness
"""
from typing import Any, Dict, Optional, List
import aiohttp
from ...base import BaseNode
from ...registry import register_node

@register_node("fitbit_node")
class FitbitNode(BaseNode):
    """
    Retrieve biometric and activity data via the Fitbit Web API.
    """
    node_type = "fitbit_node"
    version = "1.0.0"
    category = "health"
    credentials_required = ["fitbit_auth"]

    inputs = {
        "action": {
            "type": "dropdown",
            "default": "get_profile",
            "options": ["get_profile", "get_sleep_logs", "get_heart_rate"],
            "description": "Fitbit action"
        },
        "date": {
            "type": "string",
            "optional": True,
            "description": "YYYY-MM-DD"
        }
    }

    outputs = {
        "result": {"type": "any"},
        "status": {"type": "string"}
    }

    async def execute(self, input_data: Any, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        try:
            creds = await self.get_credential("fitbit_auth")
            access_token = creds.get("access_token") if creds else self.get_config("access_token")
            
            if not access_token:
                return {"status": "error", "error": "Fitbit OAuth Access Token is required."}

            headers = {
                "Authorization": f"Bearer {access_token}",
                "Accept": "application/json"
            }
            
            base_url = "https://api.fitbit.com/1"
            action = self.get_config("action", "get_profile")
            date = self.get_config("date", "today")

            async with aiohttp.ClientSession() as session:
                if action == "get_profile":
                    url = f"{base_url}/user/-/profile.json"
                    async with session.get(url, headers=headers) as resp:
                        res_data = await resp.json()
                        return {"status": "success", "data": {"result": res_data.get("user")}}

                elif action == "get_sleep_logs":
                    url = f"{base_url}/user/-/sleep/date/{date}.json"
                    async with session.get(url, headers=headers) as resp:
                        res_data = await resp.json()
                        return {"status": "success", "data": {"result": res_data.get("sleep", [])}}

                elif action == "get_heart_rate":
                    # Time series heart rate
                    url = f"{base_url}/user/-/activities/heart/date/{date}/1d.json"
                    async with session.get(url, headers=headers) as resp:
                        res_data = await resp.json()
                        return {"status": "success", "data": {"result": res_data.get("activities-heart", [])}}

                return {"status": "error", "error": f"Unsupported action: {action}"}

        except Exception as e:
            return {"status": "error", "error": f"Fitbit Node Failed: {str(e)}"}
