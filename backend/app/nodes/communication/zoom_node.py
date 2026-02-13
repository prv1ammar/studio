"""
Zoom Node - Studio Standard (Universal Method)
Batch 89: Core Workflow Nodes
"""
from typing import Any, Dict, Optional, List
import aiohttp
from ...base import BaseNode
from ...registry import register_node

@register_node("zoom_node")
class ZoomNode(BaseNode):
    """
    Manage Zoom meetings, webinars, and users via Zoom API.
    """
    node_type = "zoom_node"
    version = "1.0.0"
    category = "communication"
    credentials_required = ["zoom_auth"]

    inputs = {
        "action": {
            "type": "dropdown",
            "default": "create_meeting",
            "options": ["create_meeting", "list_meetings", "get_meeting", "delete_meeting", "list_users"],
            "description": "Zoom action"
        },
        "topic": {
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
        "status": {"type": "string"},
        "join_url": {"type": "string", "optional": True}
    }

    async def execute(self, input_data: Any, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        try:
            # 1. Authentication (OAuth 2.0 / JWT)
            creds = await self.get_credential("zoom_auth")
            access_token = creds.get("access_token")
            
            if not access_token:
                return {"status": "error", "error": "Zoom Access Token required."}

            headers = {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json"
            }
            
            # 2. Connect to Real API
            base_url = "https://api.zoom.us/v2"
            action = self.get_config("action", "create_meeting")

            async with aiohttp.ClientSession() as session:
                if action == "create_meeting":
                    topic = self.get_config("topic") or "Studio Workflow Meeting"
                    url = f"{base_url}/users/me/meetings"
                    payload = {
                        "topic": topic,
                        "type": 2,  # Scheduled meeting
                        "settings": {
                            "host_video": True,
                            "participant_video": True
                        }
                    }
                    async with session.post(url, headers=headers, json=payload) as resp:
                        if resp.status not in [200, 201]:
                            return {"status": "error", "error": f"Zoom API Error: {resp.status}"}
                        res_data = await resp.json()
                        return {
                            "status": "success",
                            "data": {
                                "result": res_data,
                                "join_url": res_data.get("join_url")
                            }
                        }

                elif action == "list_meetings":
                    url = f"{base_url}/users/me/meetings"
                    async with session.get(url, headers=headers) as resp:
                        if resp.status != 200:
                            return {"status": "error", "error": f"Zoom API Error: {resp.status}"}
                        res_data = await resp.json()
                        return {"status": "success", "data": {"result": res_data.get("meetings", [])}}

                elif action == "get_meeting":
                    meeting_id = self.get_config("meeting_id") or str(input_data)
                    url = f"{base_url}/meetings/{meeting_id}"
                    async with session.get(url, headers=headers) as resp:
                        if resp.status != 200:
                            return {"status": "error", "error": f"Zoom API Error: {resp.status}"}
                        res_data = await resp.json()
                        return {"status": "success", "data": {"result": res_data}}

                return {"status": "error", "error": f"Unsupported action: {action}"}

        except Exception as e:
            return {"status": "error", "error": f"Zoom Node Failed: {str(e)}"}
