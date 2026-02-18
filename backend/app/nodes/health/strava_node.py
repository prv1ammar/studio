"""
Strava Node - Studio Standard
Batch 77: Health & Fitness
"""
from typing import Any, Dict, Optional, List
import aiohttp
from ..base import BaseNode
from ..registry import register_node

@register_node("strava_node")
class StravaNode(BaseNode):
    """
    Access athlete activities and statistics via the Strava API v3.
    """
    node_type = "strava_node"
    version = "1.0.0"
    category = "health"
    credentials_required = ["strava_auth"]


    properties = [
        {
            'displayName': 'Operation',
            'name': 'operation',
            'type': 'options',
            'default': 'list_activities',
            'options': [
                {'name': 'List Activities', 'value': 'list_activities'},
                {'name': 'Get Athlete Profile', 'value': 'get_athlete_profile'},
                {'name': 'Get Stats', 'value': 'get_stats'},
            ],
            'description': 'Strava action',
        },
        {
            'displayName': 'Athlete Id',
            'name': 'athlete_id',
            'type': 'string',
            'default': '',
            'description': 'Required for stats',
        },
    ]
    inputs = {
        "action": {
            "type": "dropdown",
            "default": "list_activities",
            "options": ["list_activities", "get_athlete_profile", "get_stats"],
            "description": "Strava action"
        },
        "athlete_id": {
            "type": "string",
            "optional": True,
            "description": "Required for stats"
        }
    }

    outputs = {
        "result": {"type": "any"},
        "status": {"type": "string"},
        "count": {"type": "number"}
    }

    async def execute(self, input_data: Any, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        try:
            creds = await self.get_credential("strava_auth")
            access_token = creds.get("access_token") if creds else self.get_config("access_token")
            
            if not access_token:
                return {"status": "error", "error": "Strava Access Token is required."}

            headers = {
                "Authorization": f"Bearer {access_token}",
                "Accept": "application/json"
            }
            
            base_url = "https://www.strava.com/api/v3"
            action = self.get_config("action", "list_activities")

            async with aiohttp.ClientSession() as session:
                if action == "list_activities":
                    url = f"{base_url}/athlete/activities"
                    async with session.get(url, headers=headers) as resp:
                        res_data = await resp.json()
                        return {"status": "success", "data": {"result": res_data, "count": len(res_data) if isinstance(res_data, list) else 0}}

                elif action == "get_athlete_profile":
                    url = f"{base_url}/athlete"
                    async with session.get(url, headers=headers) as resp:
                        res_data = await resp.json()
                        return {"status": "success", "data": {"result": res_data}}

                elif action == "get_stats":
                    a_id = self.get_config("athlete_id") or str(input_data)
                    if not a_id:
                        return {"status": "error", "error": "athlete_id is required for stats."}
                    url = f"{base_url}/athletes/{a_id}/stats"
                    async with session.get(url, headers=headers) as resp:
                        res_data = await resp.json()
                        return {"status": "success", "data": {"result": res_data}}

                return {"status": "error", "error": f"Unsupported action: {action}"}

        except Exception as e:
            return {"status": "error", "error": f"Strava Node Failed: {str(e)}"}