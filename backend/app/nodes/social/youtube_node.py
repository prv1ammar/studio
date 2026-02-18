"""
YouTube Node - Studio Standard (Universal Method)
Batch 92: Social Media Integration (n8n Critical)
"""
from typing import Any, Dict, Optional, List
import aiohttp
from ..base import BaseNode
from ..registry import register_node

@register_node("youtube_node")
class YouTubeNode(BaseNode):
    """
    Manage YouTube channels, videos, and comments via YouTube Data API v3.
    """
    node_type = "youtube_node"
    version = "1.0.0"
    category = "social"
    credentials_required = ["google_auth"]


    properties = [
        {
            'displayName': 'Operation',
            'name': 'operation',
            'type': 'options',
            'default': 'get_channel_stats',
            'options': [
                {'name': 'Get Channel Stats', 'value': 'get_channel_stats'},
                {'name': 'Search Videos', 'value': 'search_videos'},
                {'name': 'Get Video Details', 'value': 'get_video_details'},
                {'name': 'Insert Comment', 'value': 'insert_comment'},
            ],
            'description': 'YouTube action',
        },
        {
            'displayName': 'Comment Text',
            'name': 'comment_text',
            'type': 'string',
            'default': '',
        },
        {
            'displayName': 'Query',
            'name': 'query',
            'type': 'string',
            'default': '',
        },
        {
            'displayName': 'Video Id',
            'name': 'video_id',
            'type': 'string',
            'default': '',
        },
    ]
    inputs = {
        "action": {
            "type": "dropdown",
            "default": "get_channel_stats",
            "options": ["get_channel_stats", "search_videos", "get_video_details", "insert_comment"],
            "description": "YouTube action"
        },
        "query": {
            "type": "string",
            "optional": True
        },
        "video_id": {
            "type": "string",
            "optional": True
        },
        "comment_text": {
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

            # 2. Connect to Real API
            base_url = "https://www.googleapis.com/youtube/v3"
            action = self.get_config("action", "get_channel_stats")

            async with aiohttp.ClientSession() as session:
                headers = {"Authorization": f"Bearer {access_token}"}
                
                if action == "get_channel_stats":
                    url = f"{base_url}/channels"
                    params = {"mine": "true", "part": "statistics,snippet"}
                    async with session.get(url, headers=headers, params=params) as resp:
                        if resp.status != 200:
                            return {"status": "error", "error": f"YouTube API Error: {resp.status}"}
                        res_data = await resp.json()
                        return {"status": "success", "data": {"result": res_data.get("items", [])}}

                elif action == "search_videos":
                    query = self.get_config("query") or str(input_data)
                    url = f"{base_url}/search"
                    params = {"q": query, "part": "snippet", "maxResults": 10, "type": "video"}
                    async with session.get(url, headers=headers, params=params) as resp:
                        if resp.status != 200:
                            return {"status": "error", "error": f"YouTube API Error: {resp.status}"}
                        res_data = await resp.json()
                        return {"status": "success", "data": {"result": res_data.get("items", [])}}

                elif action == "get_video_details":
                    video_id = self.get_config("video_id") or str(input_data)
                    url = f"{base_url}/videos"
                    params = {"id": video_id, "part": "snippet,statistics"}
                    async with session.get(url, headers=headers, params=params) as resp:
                        if resp.status != 200:
                            return {"status": "error", "error": f"YouTube API Error: {resp.status}"}
                        res_data = await resp.json()
                        return {"status": "success", "data": {"result": res_data.get("items", [])}}

                elif action == "insert_comment":
                    video_id = self.get_config("video_id")
                    comment_text = self.get_config("comment_text") or str(input_data)
                    
                    if not video_id:
                        return {"status": "error", "error": "video_id required for comment"}
                    
                    url = f"{base_url}/commentThreads"
                    params = {"part": "snippet"}
                    payload = {
                        "snippet": {
                            "videoId": video_id,
                            "topLevelComment": {
                                "snippet": {
                                    "textOriginal": comment_text
                                }
                            }
                        }
                    }
                    async with session.post(url, headers=headers, params=params, json=payload) as resp:
                        if resp.status not in [200, 201]:
                            return {"status": "error", "error": f"YouTube Comment Error: {resp.status}"}
                        res_data = await resp.json()
                        return {"status": "success", "data": {"result": res_data}}

                return {"status": "error", "error": f"Unsupported action: {action}"}

        except Exception as e:
            return {"status": "error", "error": f"YouTube Node Failed: {str(e)}"}