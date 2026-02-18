"""
Facebook Node - Studio Standard (Universal Method)
Batch 92: Social Media Integration (n8n Critical)
"""
from typing import Any, Dict, Optional, List
import aiohttp
from ..base import BaseNode
from ..registry import register_node

@register_node("facebook_node")
class FacebookNode(BaseNode):
    """
    Manage Facebook pages, posts, and ads via Facebook Graph API.
    """
    node_type = "facebook_node"
    version = "1.0.0"
    category = "social"
    credentials_required = ["facebook_auth"]


    properties = [
        {
            'displayName': 'Operation',
            'name': 'operation',
            'type': 'options',
            'default': 'create_post',
            'options': [
                {'name': 'Create Post', 'value': 'create_post'},
                {'name': 'Get Page Posts', 'value': 'get_page_posts'},
                {'name': 'Get Page Info', 'value': 'get_page_info'},
                {'name': 'Create Photo Post', 'value': 'create_photo_post'},
            ],
            'description': 'Facebook action',
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
    ]
    inputs = {
        "action": {
            "type": "dropdown",
            "default": "create_post",
            "options": ["create_post", "get_page_posts", "get_page_info", "create_photo_post"],
            "description": "Facebook action"
        },
        "page_id": {
            "type": "string",
            "optional": True
        },
        "message": {
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
            creds = await self.get_credential("facebook_auth")
            access_token = creds.get("access_token")
            
            if not access_token:
                return {"status": "error", "error": "Facebook Access Token required."}

            # 2. Connect to Real API
            base_url = "https://graph.facebook.com/v18.0"
            action = self.get_config("action", "create_post")
            page_id = self.get_config("page_id")

            async with aiohttp.ClientSession() as session:
                if action == "create_post":
                    message = self.get_config("message") or str(input_data)
                    
                    if not page_id:
                        return {"status": "error", "error": "page_id required"}
                    
                    url = f"{base_url}/{page_id}/feed"
                    params = {
                        "message": message,
                        "access_token": access_token
                    }
                    async with session.post(url, params=params) as resp:
                        if resp.status not in [200, 201]:
                            return {"status": "error", "error": f"Facebook Error: {resp.status} - {await resp.text()}"}
                        res_data = await resp.json()
                        return {"status": "success", "data": {"result": res_data}}

                elif action == "get_page_posts":
                    if not page_id:
                        return {"status": "error", "error": "page_id required"}
                    
                    url = f"{base_url}/{page_id}/posts"
                    params = {"access_token": access_token, "limit": 10}
                    async with session.get(url, params=params) as resp:
                        if resp.status != 200:
                            return {"status": "error", "error": f"Facebook Error: {resp.status}"}
                        res_data = await resp.json()
                        return {"status": "success", "data": {"result": res_data.get("data", [])}}

                elif action == "get_page_info":
                    if not page_id:
                        return {"status": "error", "error": "page_id required"}
                    
                    url = f"{base_url}/{page_id}"
                    params = {
                        "fields": "id,name,about,followers_count,fan_count",
                        "access_token": access_token
                    }
                    async with session.get(url, params=params) as resp:
                        if resp.status != 200:
                            return {"status": "error", "error": f"Facebook Error: {resp.status}"}
                        res_data = await resp.json()
                        return {"status": "success", "data": {"result": res_data}}

                return {"status": "error", "error": f"Unsupported action: {action}"}

        except Exception as e:
            return {"status": "error", "error": f"Facebook Node Failed: {str(e)}"}