"""
Zoom Node - Studio Standard (Universal Method)
Batch 104: Communication Essentials
"""
from typing import Any, Dict, Optional
import aiohttp
from ..base import BaseNode
from ..registry import register_node

@register_node("zoom_node")
class ZoomNode(BaseNode):
    """
    Zoom video conferencing integration.
    """
    node_type = "zoom_node"
    version = "1.0.0"
    category = "communication"
    credentials_required = ["zoom_auth"]


    properties = [
        {
            'displayName': 'Operation',
            'name': 'operation',
            'type': 'options',
            'default': 'create_meeting',
            'options': [
                {'name': 'Create Meeting', 'value': 'create_meeting'},
                {'name': 'List Meetings', 'value': 'list_meetings'},
                {'name': 'Get Meeting', 'value': 'get_meeting'},
                {'name': 'Delete Meeting', 'value': 'delete_meeting'},
                {'name': 'List Users', 'value': 'list_users'},
                {'name': 'Create Webinar', 'value': 'create_webinar'},
            ],
            'description': 'Zoom action',
        },
        {
            'displayName': 'Duration',
            'name': 'duration',
            'type': 'string',
            'default': 60,
        },
        {
            'displayName': 'Meeting Id',
            'name': 'meeting_id',
            'type': 'string',
            'default': '',
        },
        {
            'displayName': 'Start Time',
            'name': 'start_time',
            'type': 'string',
            'default': '',
        },
        {
            'displayName': 'Topic',
            'name': 'topic',
            'type': 'string',
            'default': '',
        },
    ]
    inputs = {
        "action": {
            "type": "dropdown",
            "default": "create_meeting",
            "options": ["create_meeting", "list_meetings", "get_meeting", "delete_meeting", "list_users", "create_webinar"],
            "description": "Zoom action"
        },
        "topic": {
            "type": "string",
            "optional": True
        },
        "duration": {
            "type": "number",
            "default": 60,
            "optional": True
        },
        "start_time": {
            "type": "string",
            "optional": True
        },
        "meeting_id": {
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
            creds = await self.get_credential("zoom_auth")
            access_token = creds.get("access_token") or creds.get("jwt_token")
            
            if not access_token:
                return {"status": "error", "error": "Zoom access token required"}

            base_url = "https://api.zoom.us/v2"
            headers = {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json"
            }
            
            action = self.get_config("action", "create_meeting")

            async with aiohttp.ClientSession() as session:
                if action == "create_meeting":
                    topic = self.get_config("topic", "Studio Meeting")
                    duration = int(self.get_config("duration", 60))
                    start_time = self.get_config("start_time")
                    
                    url = f"{base_url}/users/me/meetings"
                    payload = {
                        "topic": topic,
                        "type": 2,  # Scheduled meeting
                        "duration": duration,
                        "settings": {
                            "host_video": True,
                            "participant_video": True
                        }
                    }
                    
                    if start_time:
                        payload["start_time"] = start_time
                    
                    async with session.post(url, headers=headers, json=payload) as resp:
                        if resp.status not in [200, 201]:
                            error_text = await resp.text()
                            return {"status": "error", "error": f"Zoom API Error {resp.status}: {error_text}"}
                        res_data = await resp.json()
                        return {"status": "success", "data": {"result": res_data}}

                elif action == "list_meetings":
                    url = f"{base_url}/users/me/meetings"
                    async with session.get(url, headers=headers) as resp:
                        if resp.status != 200:
                            error_text = await resp.text()
                            return {"status": "error", "error": f"Zoom API Error {resp.status}: {error_text}"}
                        res_data = await resp.json()
                        return {"status": "success", "data": {"result": res_data.get("meetings", [])}}

                elif action == "get_meeting":
                    meeting_id = self.get_config("meeting_id") or str(input_data)
                    if not meeting_id:
                        return {"status": "error", "error": "meeting_id required"}
                    
                    url = f"{base_url}/meetings/{meeting_id}"
                    async with session.get(url, headers=headers) as resp:
                        if resp.status != 200:
                            error_text = await resp.text()
                            return {"status": "error", "error": f"Zoom API Error {resp.status}: {error_text}"}
                        res_data = await resp.json()
                        return {"status": "success", "data": {"result": res_data}}

                elif action == "delete_meeting":
                    meeting_id = self.get_config("meeting_id") or str(input_data)
                    if not meeting_id:
                        return {"status": "error", "error": "meeting_id required"}
                    
                    url = f"{base_url}/meetings/{meeting_id}"
                    async with session.delete(url, headers=headers) as resp:
                        if resp.status not in [200, 204]:
                            error_text = await resp.text()
                            return {"status": "error", "error": f"Zoom API Error {resp.status}: {error_text}"}
                        return {"status": "success", "data": {"result": {"message": "Meeting deleted"}}}

                return {"status": "error", "error": f"Unsupported action: {action}"}

        except Exception as e:
            return {"status": "error", "error": f"Zoom Node Failed: {str(e)}"}