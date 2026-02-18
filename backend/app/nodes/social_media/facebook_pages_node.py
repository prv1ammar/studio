"""
Facebook Pages Node - Studio Standard (Universal Method)
Batch 106: Social Media
"""
from typing import Any, Dict, Optional
import aiohttp
from ..base import BaseNode
from ..registry import register_node

@register_node("facebook_pages_node")
class FacebookPagesNode(BaseNode):
    """
    Facebook Pages integration for publishing and management.
    """
    node_type = "facebook_pages_node"
    version = "1.0.0"
    category = "social_media"
    credentials_required = ["facebook_graph_auth"]


    properties = [
        {
            'displayName': 'Operation',
            'name': 'operation',
            'type': 'options',
            'default': 'create_post',
            'options': [
                {'name': 'Create Post', 'value': 'create_post'},
                {'name': 'Get Posts', 'value': 'get_posts'},
                {'name': 'Get Page Info', 'value': 'get_page_info'},
                {'name': 'Upload Photo', 'value': 'upload_photo'},
            ],
            'description': 'Facebook action',
        },
        {
            'displayName': 'Link',
            'name': 'link',
            'type': 'string',
            'default': '',
        },
        {
            'displayName': 'Message',
            'name': 'message',
            'type': 'string',
            'default': '',
        },
        {
            'displayName': 'Page Id',
            'name': 'page_id',
            'type': 'string',
            'default': '',
        },
        {
            'displayName': 'Photo Url',
            'name': 'photo_url',
            'type': 'string',
            'default': '',
        },
    ]
    inputs = {
        "action": {
            "type": "dropdown",
            "default": "create_post",
            "options": ["create_post", "get_posts", "get_page_info", "upload_photo"],
            "description": "Facebook action"
        },
        "page_id": {
            "type": "string",
            "optional": True
        },
        "message": {
            "type": "string",
            "optional": True
        },
        "link": {
            "type": "string",
            "optional": True
        },
        "photo_url": {
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
            creds = await self.get_credential("facebook_graph_auth")
            access_token = creds.get("page_access_token") or creds.get("access_token")
            
            if not access_token:
                return {"status": "error", "error": "Facebook Page access token required"}

            base_url = "https://graph.facebook.com/v19.0"
            
            action = self.get_config("action", "create_post")
            page_id = self.get_config("page_id", "me")

            async with aiohttp.ClientSession() as session:
                if action == "create_post":
                    message = self.get_config("message")
                    link = self.get_config("link")
                    
                    if not message:
                        return {"status": "error", "error": "message required"}
                    
                    url = f"{base_url}/{page_id}/feed"
                    payload = {"message": message, "access_token": access_token}
                    if link:
                        payload["link"] = link
                    
                    async with session.post(url, json=payload) as resp:
                        if resp.status != 200:
                            error_text = await resp.text()
                            return {"status": "error", "error": f"Facebook API Error {resp.status}: {error_text}"}
                        res_data = await resp.json()
                        return {"status": "success", "data": {"result": res_data}}

                elif action == "upload_photo":
                    photo_url = self.get_config("photo_url")
                    message = self.get_config("message")
                    
                    if not photo_url:
                        return {"status": "error", "error": "photo_url required"}
                    
                    url = f"{base_url}/{page_id}/photos"
                    payload = {
                        "url": photo_url, 
                        "access_token": access_token
                    }
                    if message:
                        payload["message"] = message
                        
                    async with session.post(url, json=payload) as resp:
                         if resp.status != 200:
                            error_text = await resp.text()
                            return {"status": "error", "error": f"Facebook API Error {resp.status}: {error_text}"}
                         res_data = await resp.json()
                         return {"status": "success", "data": {"result": res_data}}

                elif action == "get_posts":
                    url = f"{base_url}/{page_id}/feed"
                    params = {"access_token": access_token}
                    async with session.get(url, params=params) as resp:
                        if resp.status != 200:
                            error_text = await resp.text()
                            return {"status": "error", "error": f"Facebook API Error {resp.status}: {error_text}"}
                        res_data = await resp.json()
                        return {"status": "success", "data": {"result": res_data.get("data", [])}}

            return {"status": "error", "error": f"Unsupported action: {action}"}

        except Exception as e:
            return {"status": "error", "error": f"Facebook Node Failed: {str(e)}"}