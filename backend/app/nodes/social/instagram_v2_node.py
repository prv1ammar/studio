"""
Instagram Node - Studio Standard (Universal Method)
Batch 92: Social Media Integration (n8n Critical)
"""
from typing import Any, Dict, Optional, List
import aiohttp
from ...base import BaseNode
from ...registry import register_node

@register_node("instagram_v2_node")
class InstagramV2Node(BaseNode):
    """
    Manage Instagram media and insights via Graph API.
    """
    node_type = "instagram_v2_node"
    version = "1.0.0"
    category = "social"
    credentials_required = ["facebook_auth"]  # Uses Facebook OAuth

    inputs = {
        "action": {
            "type": "dropdown",
            "default": "get_media",
            "options": ["get_media", "publish_media", "get_account_info", "get_comments"],
            "description": "Instagram action"
        },
        "ig_user_id": {
            "type": "string",
            "required": True
        },
        "image_url": {
            "type": "string",
            "optional": True
        },
        "caption": {
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
                return {"status": "error", "error": "Instagram/Facebook Access Token required."}

            base_url = "https://graph.facebook.com/v18.0"
            ig_user_id = self.get_config("ig_user_id")
            action = self.get_config("action", "get_media")

            async with aiohttp.ClientSession() as session:
                if action == "get_account_info":
                    url = f"{base_url}/{ig_user_id}"
                    params = {
                        "fields": "biography,followers_count,follows_count,media_count,name,profile_picture_url,username",
                        "access_token": access_token
                    }
                    async with session.get(url, params=params) as resp:
                        if resp.status != 200:
                            return {"status": "error", "error": f"Instagram API Error: {resp.status}"}
                        res_data = await resp.json()
                        return {"status": "success", "data": {"result": res_data}}

                elif action == "get_media":
                    url = f"{base_url}/{ig_user_id}/media"
                    params = {
                        "fields": "id,caption,media_type,media_url,permalink,timestamp,like_count,comments_count",
                        "access_token": access_token,
                        "limit": 10
                    }
                    async with session.get(url, params=params) as resp:
                        if resp.status != 200:
                            return {"status": "error", "error": f"Instagram API Error: {resp.status}"}
                        res_data = await resp.json()
                        return {"status": "success", "data": {"result": res_data.get("data", [])}}

                elif action == "publish_media":
                    # Two-step process: Create Container -> Publish Container
                    image_url = self.get_config("image_url")
                    caption = self.get_config("caption") or str(input_data)
                    
                    if not image_url:
                        return {"status": "error", "error": "image_url required for publishing"}
                    
                    # Step 1: Create Container
                    url_create = f"{base_url}/{ig_user_id}/media"
                    params_create = {
                        "image_url": image_url,
                        "caption": caption,
                        "access_token": access_token
                    }
                    async with session.post(url_create, params=params_create) as resp:
                        if resp.status != 200:
                            return {"status": "error", "error": f"Instagram Container Error: {resp.status}"}
                        create_data = await resp.json() 
                        container_id = create_data.get("id")

                    # Step 2: Publish Container
                    url_publish = f"{base_url}/{ig_user_id}/media_publish"
                    params_publish = {
                        "creation_id": container_id,
                        "access_token": access_token
                    }
                    async with session.post(url_publish, params=params_publish) as resp:
                         if resp.status != 200:
                            return {"status": "error", "error": f"Instagram Publish Error: {resp.status}"}
                         res_data = await resp.json()
                         return {"status": "success", "data": {"result": res_data}}

                return {"status": "error", "error": f"Unsupported action: {action}"}

        except Exception as e:
            return {"status": "error", "error": f"Instagram Node Failed: {str(e)}"}
