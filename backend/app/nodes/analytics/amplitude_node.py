"""
Amplitude Node - Studio Standard
Batch 70: Advanced Analytics
"""
from typing import Any, Dict, Optional, List
import aiohttp
import base64
from ..base import BaseNode
from ..registry import register_node

@register_node("amplitude_node")
class AmplitudeNode(BaseNode):
    """
    Retrieve user insights and track behavioral events via Amplitude.
    """
    node_type = "amplitude_node"
    version = "1.0.0"
    category = "analytics"
    credentials_required = ["amplitude_auth"]


    properties = [
        {
            'displayName': 'Operation',
            'name': 'operation',
            'type': 'options',
            'default': 'get_user_profile',
            'options': [
                {'name': 'Get User Profile', 'value': 'get_user_profile'},
                {'name': 'Track Event', 'value': 'track_event'},
                {'name': 'Get Active Users', 'value': 'get_active_users'},
                {'name': 'List Cohorts', 'value': 'list_cohorts'},
            ],
            'description': 'Amplitude action',
        },
        {
            'displayName': 'Event Type',
            'name': 'event_type',
            'type': 'string',
            'default': '',
            'description': 'Type/Name of the event to track',
        },
        {
            'displayName': 'User Id',
            'name': 'user_id',
            'type': 'string',
            'default': '',
            'description': 'Unique ID of the user',
        },
    ]
    inputs = {
        "action": {
            "type": "dropdown",
            "default": "get_user_profile",
            "options": ["get_user_profile", "track_event", "get_active_users", "list_cohorts"],
            "description": "Amplitude action"
        },
        "user_id": {
            "type": "string",
            "optional": True,
            "description": "Unique ID of the user"
        },
        "event_type": {
            "type": "string",
            "optional": True,
            "description": "Type/Name of the event to track"
        }
    }

    outputs = {
        "result": {"type": "any"},
        "status": {"type": "string"}
    }

    async def execute(self, input_data: Any, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        try:
            creds = await self.get_credential("amplitude_auth")
            api_key = creds.get("api_key") if creds else self.get_config("api_key")
            secret_key = creds.get("secret_key") if creds else self.get_config("secret_key")
            
            if not api_key:
                return {"status": "error", "error": "Amplitude API Key is required."}

            headers = {
                "Content-Type": "application/json"
            }
            
            # Auth for Dashboard/Export API (Management)
            auth_str = f"{api_key}:{secret_key}"
            encoded_auth = base64.b64encode(auth_str.encode()).decode()
            mgr_headers = {**headers, "Authorization": f"Basic {encoded_auth}"}
            
            action = self.get_config("action", "get_user_profile")

            async with aiohttp.ClientSession() as session:
                if action == "get_user_profile":
                    user_id = self.get_config("user_id") or str(input_data)
                    # Behavioral Graph API
                    url = f"https://amplitude.com/api/2/userprofile?user_id={user_id}"
                    async with session.get(url, headers=mgr_headers) as resp:
                        res_data = await resp.json()
                        return {"status": "success", "data": {"result": res_data}}

                elif action == "track_event":
                    # HTTP V2 API (Ingest)
                    url = "https://api2.amplitude.com/2/httpapi"
                    user_id = self.get_config("user_id") or "studio_agent"
                    event_type = self.get_config("event_type") or "agent_execution"
                    payload = {
                        "api_key": api_key,
                        "events": [
                            {
                                "user_id": user_id,
                                "event_type": event_type,
                                "user_properties": {"source": "studio"}
                            }
                        ]
                    }
                    async with session.post(url, headers=headers, json=payload) as resp:
                        res_data = await resp.json()
                        return {"status": "success", "data": {"result": res_data, "status": "tracked"}}

                elif action == "list_cohorts":
                    url = "https://amplitude.com/api/3/cohorts"
                    async with session.get(url, headers=mgr_headers) as resp:
                        res_data = await resp.json()
                        return {"status": "success", "data": {"result": res_data.get("cohorts", [])}}

                return {"status": "error", "error": f"Unsupported action: {action}"}

        except Exception as e:
            return {"status": "error", "error": f"Amplitude Node Failed: {str(e)}"}