"""
Later Node - Studio Standard (Universal Method)
Batch 106: Social Media
"""
from typing import Any, Dict, Optional
import aiohttp
from ..base import BaseNode
from ..registry import register_node

@register_node("later_node")
class LaterNode(BaseNode):
    """
    Later integration for visual social marketing.
    """
    node_type = "later_node"
    version = "1.0.0"
    category = "social_media"
    credentials_required = ["later_auth"]


    properties = [
        {
            'displayName': 'Operation',
            'name': 'operation',
            'type': 'options',
            'default': 'upload_media',
            'options': [
                {'name': 'Upload Media', 'value': 'upload_media'},
                {'name': 'Get User', 'value': 'get_user'},
            ],
            'description': 'Later action',
        },
        {
            'displayName': 'Image Url',
            'name': 'image_url',
            'type': 'string',
            'default': '',
        },
    ]
    inputs = {
        "action": {
            "type": "dropdown",
            "default": "upload_media",
            "options": ["upload_media", "get_user"],
            "description": "Later action"
        },
        "image_url": {
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
            creds = await self.get_credential("later_auth")
            access_token = creds.get("access_token")
            
            if not access_token:
                return {"status": "error", "error": "Later access token required"}

            base_url = "https://api.later.com/v1"
            headers = {"Authorization": f"Bearer {access_token}"}
            
            action = self.get_config("action", "upload_media")

            async with aiohttp.ClientSession() as session:
                if action == "upload_media":
                    image_url = self.get_config("image_url")
                    if not image_url:
                        return {"status": "error", "error": "image_url required"}
                    
                    # Later API for media upload usually involves multiple steps or just pointing to URL
                    # Simplified for initial implementation:
                    url = f"{base_url}/media"
                    payload = {"url": image_url}
                    
                    async with session.post(url, headers=headers, json=payload) as resp:
                        if resp.status != 200:
                            error_text = await resp.text()
                            return {"status": "error", "error": f"Later API Error {resp.status}: {error_text}"}
                        res_data = await resp.json()
                        return {"status": "success", "data": {"result": res_data}}

                elif action == "get_user":
                    url = f"{base_url}/users/me"
                    async with session.get(url, headers=headers) as resp:
                        if resp.status != 200:
                            error_text = await resp.text()
                            return {"status": "error", "error": f"Later API Error {resp.status}: {error_text}"}
                        res_data = await resp.json()
                        return {"status": "success", "data": {"result": res_data}}

            return {"status": "error", "error": f"Unsupported action: {action}"}

        except Exception as e:
            return {"status": "error", "error": f"Later Node Failed: {str(e)}"}