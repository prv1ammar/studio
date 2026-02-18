"""
Google Calendar Node - Studio Standard (Universal Method)
Batch 90: CRM & Marketing (n8n Critical)
"""
from typing import Any, Dict, Optional, List
import aiohttp
from datetime import datetime, timedelta
from ..base import BaseNode
from ..registry import register_node

@register_node("google_calendar_node")
class GoogleCalendarNode(BaseNode):
    """
    Manage events in Google Calendar via Google Calendar API.
    """
    node_type = "google_calendar_node"
    version = "1.0.0"
    category = "productivity"
    credentials_required = ["google_auth"]


    properties = [
        {
            'displayName': 'Operation',
            'name': 'operation',
            'type': 'options',
            'default': 'create_event',
            'options': [
                {'name': 'Create Event', 'value': 'create_event'},
                {'name': 'List Events', 'value': 'list_events'},
                {'name': 'Get Event', 'value': 'get_event'},
                {'name': 'Update Event', 'value': 'update_event'},
                {'name': 'Delete Event', 'value': 'delete_event'},
            ],
            'description': 'Google Calendar action',
        },
        {
            'displayName': 'Calendar Id',
            'name': 'calendar_id',
            'type': 'string',
            'default': 'primary',
            'description': 'Calendar ID (default: primary)',
        },
        {
            'displayName': 'Start Time',
            'name': 'start_time',
            'type': 'string',
            'default': '',
        },
        {
            'displayName': 'Summary',
            'name': 'summary',
            'type': 'string',
            'default': '',
        },
    ]
    inputs = {
        "action": {
            "type": "dropdown",
            "default": "create_event",
            "options": ["create_event", "list_events", "get_event", "update_event", "delete_event"],
            "description": "Google Calendar action"
        },
        "calendar_id": {
            "type": "string",
            "default": "primary",
            "description": "Calendar ID (default: primary)"
        },
        "summary": {
            "type": "string",
            "optional": True
        },
        "start_time": {
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
            creds = await self.get_credential("google_auth")
            access_token = creds.get("access_token")
            
            if not access_token:
                return {"status": "error", "error": "Google Access Token required."}

            headers = {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json"
            }
            
            # 2. Connect to Real API
            base_url = "https://www.googleapis.com/calendar/v3"
            action = self.get_config("action", "create_event")
            calendar_id = self.get_config("calendar_id", "primary")

            async with aiohttp.ClientSession() as session:
                if action == "create_event":
                    summary = self.get_config("summary") or str(input_data)
                    start_time = self.get_config("start_time")
                    
                    # Default to 1 hour from now if no time specified
                    if not start_time:
                        start_dt = datetime.utcnow() + timedelta(hours=1)
                        end_dt = start_dt + timedelta(hours=1)
                        start_time = start_dt.isoformat() + "Z"
                        end_time = end_dt.isoformat() + "Z"
                    else:
                        end_time = (datetime.fromisoformat(start_time.replace("Z", "")) + timedelta(hours=1)).isoformat() + "Z"
                    
                    url = f"{base_url}/calendars/{calendar_id}/events"
                    payload = {
                        "summary": summary,
                        "start": {"dateTime": start_time, "timeZone": "UTC"},
                        "end": {"dateTime": end_time, "timeZone": "UTC"}
                    }
                    async with session.post(url, headers=headers, json=payload) as resp:
                        if resp.status not in [200, 201]:
                            return {"status": "error", "error": f"Google Calendar Error: {resp.status}"}
                        res_data = await resp.json()
                        return {"status": "success", "data": {"result": res_data}}

                elif action == "list_events":
                    url = f"{base_url}/calendars/{calendar_id}/events"
                    params = {"maxResults": 10, "orderBy": "startTime", "singleEvents": True}
                    async with session.get(url, headers=headers, params=params) as resp:
                        if resp.status != 200:
                            return {"status": "error", "error": f"Google Calendar Error: {resp.status}"}
                        res_data = await resp.json()
                        return {"status": "success", "data": {"result": res_data.get("items", [])}}

                return {"status": "error", "error": f"Unsupported action: {action}"}

        except Exception as e:
            return {"status": "error", "error": f"Google Calendar Node Failed: {str(e)}"}