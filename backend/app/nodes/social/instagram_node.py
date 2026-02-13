"""
Instagram Business Node - Studio Standard
Batch 54: Social Engagement & Influence
"""
from typing import Any, Dict, Optional, List
import aiohttp
import asyncio
from ...base import BaseNode
from ...registry import register_node

@register_node("instagram_node")
class InstagramNode(BaseNode):
    """
    Publish content to Instagram Business accounts via the Meta Graph API.
    """
    node_type = "instagram_node"
    version = "1.0.0"
    category = "social"
    credentials_required = ["instagram_auth"]

    inputs = {
        "action": {
            "type": "dropdown",
            "default": "publish_photo",
            "options": ["publish_photo", "publish_video", "get_account_info"],
            "description": "Instagram action"
        },
        "image_url": {
            "type": "string",
            "required": True,
            "description": "URL of the image/video to publish"
        },
        "caption": {
            "type": "string",
            "optional": True,
            "description": "Post caption"
        },
        "instagram_business_id": {
            "type": "string",
            "required": True,
            "description": "The ID of the Instagram Business account"
        }
    }

    outputs = {
        "media_id": {"type": "string"},
        "permalink": {"type": "string"},
        "status": {"type": "string"}
    }

    async def execute(self, input_data: Any, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        try:
            # 1. Resolve Auth
            creds = await self.get_credential("instagram_auth")
            access_token = creds.get("access_token") if creds else self.get_config("access_token")
            business_id = self.get_config("instagram_business_id")
            
            if not access_token or not business_id:
                return {"status": "error", "error": "Instagram Access Token and Business ID are required."}

            action = self.get_config("action", "publish_photo")
            media_url = self.get_config("image_url")
            caption = self.get_config("caption", "")
            
            # Dynamic Override
            if isinstance(input_data, str) and input_data.startswith("http"):
                media_url = input_data
            elif isinstance(input_data, str):
                caption = input_data

            base_url = f"https://graph.facebook.com/v19.0/{business_id}"

            async with aiohttp.ClientSession() as session:
                # 2. Step 1: Create Media Container
                container_url = f"{base_url}/media"
                payload = {
                    "access_token": access_token,
                    "caption": caption
                }
                
                if action == "publish_photo":
                    payload["image_url"] = media_url
                elif action == "publish_video":
                    payload["video_url"] = media_url
                    payload["media_type"] = "VIDEO"
                
                async with session.post(container_url, data=payload) as resp:
                    res_data = await resp.json()
                    if resp.status >= 400:
                         return {"status": "error", "error": f"Container Creation Error: {res_data}"}
                    
                    creation_id = res_data.get("id")

                # 3. Step 2: Publish the Container
                # (Instagram sometimes requires a delay for video processing)
                if action == "publish_video":
                    await asyncio.sleep(10) # Wait for processing

                publish_url = f"{base_url}/media_publish"
                publish_payload = {
                    "creation_id": creation_id,
                    "access_token": access_token
                }
                
                async with session.post(publish_url, data=publish_payload) as resp:
                    pub_data = await resp.json()
                    if resp.status >= 400:
                         return {"status": "error", "error": f"Publishing Error: {pub_data}"}
                    
                    media_id = pub_data.get("id")
                    return {
                        "status": "success",
                        "data": {"media_id": media_id, "status": "published"}
                    }

        except Exception as e:
            return {"status": "error", "error": f"Instagram Node Failed: {str(e)}"}
