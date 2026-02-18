"""
Buffer Node - Studio Standard (Universal Method)
Batch 106: Social Media
"""
from typing import Any, Dict, Optional
import aiohttp
from ..base import BaseNode
from ..registry import register_node

@register_node("buffer_node")
class BufferNode(BaseNode):
    """
    Buffer integration for social media scheduling.
    """
    node_type = "buffer_node"
    version = "1.0.0"
    category = "social_media"
    credentials_required = ["buffer_auth"]


    properties = [
        {
            'displayName': 'Operation',
            'name': 'operation',
            'type': 'options',
            'default': 'create_update',
            'options': [
                {'name': 'Create Update', 'value': 'create_update'},
                {'name': 'Get Profiles', 'value': 'get_profiles'},
                {'name': 'Get Pending Updates', 'value': 'get_pending_updates'},
            ],
            'description': 'Buffer action',
        },
        {
            'displayName': 'Media Photo',
            'name': 'media_photo',
            'type': 'string',
            'default': '',
        },
        {
            'displayName': 'Media Thumbnail',
            'name': 'media_thumbnail',
            'type': 'string',
            'default': '',
        },
        {
            'displayName': 'Now',
            'name': 'now',
            'type': 'boolean',
            'default': False,
            'description': 'Post immediately?',
        },
        {
            'displayName': 'Profile Ids',
            'name': 'profile_ids',
            'type': 'string',
            'default': '',
            'description': 'Comma separated profile IDs',
        },
        {
            'displayName': 'Text',
            'name': 'text',
            'type': 'string',
            'default': '',
        },
    ]
    inputs = {
        "action": {
            "type": "dropdown",
            "default": "create_update",
            "options": ["create_update", "get_profiles", "get_pending_updates"],
            "description": "Buffer action"
        },
        "profile_ids": {
            "type": "string",
            "optional": True,
            "description": "Comma separated profile IDs"
        },
        "text": {
            "type": "string",
            "optional": True
        },
        "now": {
            "type": "boolean",
            "default": False,
            "optional": True,
            "description": "Post immediately?"
        },
        "media_photo": {
            "type": "string",
            "optional": True
        },
        "media_thumbnail": {
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
            creds = await self.get_credential("buffer_auth")
            access_token = creds.get("access_token")
            
            if not access_token:
                return {"status": "error", "error": "Buffer access token required"}

            base_url = "https://api.bufferapp.com/1"
            headers = {"Authorization": f"Bearer {access_token}"}
            
            action = self.get_config("action", "create_update")

            async with aiohttp.ClientSession() as session:
                if action == "create_update":
                    profile_ids = self.get_config("profile_ids")
                    text = self.get_config("text")
                    now = self.get_config("now", False)
                    
                    if not profile_ids or not text:
                        return {"status": "error", "error": "profile_ids and text required"}
                    
                    payload = {
                        "text": text,
                        "profile_ids": [pid.strip() for pid in profile_ids.split(",") if pid.strip()],
                        "now": "true" if now else "false"
                    }
                    
                    if self.get_config("media_photo"):
                        payload["media[photo]"] = self.get_config("media_photo")
                    if self.get_config("media_thumbnail"):
                        payload["media[thumbnail]"] = self.get_config("media_thumbnail")
                        
                    url = f"{base_url}/updates/create.json"
                    async with session.post(url, headers=headers, data=payload) as resp:
                         if resp.status != 200:
                            error_text = await resp.text()
                            return {"status": "error", "error": f"Buffer API Error {resp.status}: {error_text}"}
                         res_data = await resp.json()
                         return {"status": "success", "data": {"result": res_data}}

                elif action == "get_profiles":
                    url = f"{base_url}/profiles.json"
                    async with session.get(url, headers=headers) as resp:
                        if resp.status != 200:
                            error_text = await resp.text()
                            return {"status": "error", "error": f"Buffer API Error {resp.status}: {error_text}"}
                        res_data = await resp.json()
                        return {"status": "success", "data": {"result": res_data}}

            return {"status": "error", "error": f"Unsupported action: {action}"}

        except Exception as e:
            return {"status": "error", "error": f"Buffer Node Failed: {str(e)}"}