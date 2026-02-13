"""
Vimeo Node - Studio Standard
Batch 79: Media Production
"""
from typing import Any, Dict, Optional, List
import aiohttp
from ...base import BaseNode
from ...registry import register_node

@register_node("vimeo_node")
class VimeoNode(BaseNode):
    """
    Manage video uploads, projects, and privacy via the Vimeo API.
    """
    node_type = "vimeo_node"
    version = "1.0.0"
    category = "media"
    credentials_required = ["vimeo_auth"]

    inputs = {
        "action": {
            "type": "dropdown",
            "default": "list_videos",
            "options": ["list_videos", "get_video_details", "list_projects", "get_upload_quota"],
            "description": "Vimeo action"
        },
        "video_id": {
            "type": "string",
            "optional": True,
            "description": "ID of the video"
        },
        "project_id": {
            "type": "string",
            "optional": True,
            "description": "ID of the folder/project"
        }
    }

    outputs = {
        "result": {"type": "any"},
        "status": {"type": "string"},
        "count": {"type": "number"}
    }

    async def execute(self, input_data: Any, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        try:
            creds = await self.get_credential("vimeo_auth")
            access_token = creds.get("access_token") if creds else self.get_config("access_token")
            
            if not access_token:
                return {"status": "error", "error": "Vimeo Access Token is required."}

            headers = {
                "Authorization": f"Bearer {access_token}",
                "Accept": "application/vnd.vimeo.*+json;version=3.4"
            }
            
            base_url = "https://api.vimeo.com"
            action = self.get_config("action", "list_videos")

            async with aiohttp.ClientSession() as session:
                if action == "list_videos":
                    url = f"{base_url}/me/videos"
                    async with session.get(url, headers=headers) as resp:
                        res_data = await resp.json()
                        data = res_data.get("data", [])
                        return {"status": "success", "data": {"result": data, "count": len(data)}}

                elif action == "get_video_details":
                    v_id = self.get_config("video_id") or str(input_data)
                    url = f"{base_url}/videos/{v_id}"
                    async with session.get(url, headers=headers) as resp:
                        res_data = await resp.json()
                        return {"status": "success", "data": {"result": res_data}}

                elif action == "list_projects":
                    url = f"{base_url}/me/projects"
                    async with session.get(url, headers=headers) as resp:
                        res_data = await resp.json()
                        data = res_data.get("data", [])
                        return {"status": "success", "data": {"result": data, "count": len(data)}}

                elif action == "get_upload_quota":
                    url = f"{base_url}/me"
                    async with session.get(url, headers=headers) as resp:
                        res_data = await resp.json()
                        return {"status": "success", "data": {"result": res_data.get("upload_quota", {})}}

                return {"status": "error", "error": f"Unsupported action: {action}"}

        except Exception as e:
            return {"status": "error", "error": f"Vimeo Node Failed: {str(e)}"}
