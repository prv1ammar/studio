from typing import Any, Dict, Optional, List
from googleapiclient.discovery import build
from ..base import BaseNode
from ..registry import register_node
import os

@register_node("youtube_action")
class YouTubeNode(BaseNode):
    """
    Automate YouTube actions (Search, Video Details).
    """
    node_type = "youtube_action"
    version = "1.0.0"
    category = "media"
    credentials_required = ["google_auth"]

    inputs = {
        "action": {"type": "string", "default": "search", "enum": ["search", "video_details"]},
        "query_or_id": {"type": "string", "description": "Search query or Video ID"},
        "max_results": {"type": "number", "default": 5}
    }
    outputs = {
        "results": {"type": "array"},
        "details": {"type": "object"},
        "status": {"type": "string"}
    }

    async def execute(self, input_data: Any, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        try:
            # 1. Resolve Auth
            creds = await self.get_credential("google_auth")
            api_key = creds.get("api_key") if creds else self.get_config("api_key")
            
            if not api_key:
                 # Fallback to env for development
                 api_key = os.getenv("GOOGLE_API_KEY")
            
            if not api_key:
                return {"status": "error", "error": "YouTube API Key (Google Auth) is required."}

            youtube = build("youtube", "v3", developerKey=api_key)
            action = self.get_config("action", "search")
            target = str(input_data) if input_data else self.get_config("query_or_id")

            if not target:
                return {"status": "error", "error": "Input query or ID is required."}

            if action == "search":
                max_res = int(self.get_config("max_results", 5))
                request = youtube.search().list(
                    q=target,
                    part="snippet",
                    maxResults=max_res,
                    type="video"
                )
                response = request.execute()
                
                results = []
                for item in response.get("items", []):
                    results.append({
                        "id": item["id"]["videoId"],
                        "title": item["snippet"]["title"],
                        "description": item["snippet"]["description"],
                        "channel": item["snippet"]["channelTitle"],
                        "url": f"https://www.youtube.com/watch?v={item['id']['videoId']}"
                    })
                    
                return {
                    "status": "success",
                    "data": {
                        "results": results,
                        "count": len(results)
                    }
                }

            elif action == "video_details":
                request = youtube.videos().list(
                    part="snippet,statistics,contentDetails",
                    id=target
                )
                response = request.execute()
                
                if not response.get("items"):
                    return {"status": "error", "error": f"Video not found: {target}"}
                    
                item = response["items"][0]
                details = {
                    "title": item["snippet"]["title"],
                    "channel": item["snippet"]["channelTitle"],
                    "view_count": item["statistics"].get("viewCount"),
                    "like_count": item["statistics"].get("likeCount"),
                    "duration": item["contentDetails"]["duration"],
                    "published_at": item["snippet"]["publishedAt"]
                }
                return {
                    "status": "success",
                    "data": {
                        "details": details
                    }
                }

            return {"status": "error", "error": f"Unsupported YouTube action: {action}"}

        except Exception as e:
            return {"status": "error", "error": f"YouTube Node Error: {str(e)}"}
