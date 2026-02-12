from typing import Any, Dict, Optional, List
from pydantic import Field
from app.nodes.base import BaseNode, NodeConfig
from app.nodes.registry import register_node
from googleapiclient.discovery import build
import os

class YouTubeConfig(NodeConfig):
    credentials_id: Optional[str] = Field(None, description="YouTube API Key Credentials ID")
    max_results: int = Field(5, description="Max results for search")

@register_node("youtube_search")
class YouTubeSearchNode(BaseNode):
    async def execute(self, input_data: Any, context: Optional[Dict[str, Any]] = None) -> Any:
        query = input_data if isinstance(input_data, str) else input_data.get("query", "")
        max_results = self.get_config("max_results", 5)
        
        creds_data = await self.get_credential("credentials_id")
        api_key = creds_data.get("api_key") if creds_data else os.getenv("GOOGLE_API_KEY")
        
        if not api_key:
            return {"error": "YouTube/Google API Key is required."}

        try:
            youtube = build("youtube", "v3", developerKey=api_key)
            
            request = youtube.search().list(
                q=query,
                part="snippet",
                maxResults=max_results,
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
                
            return results
        except Exception as e:
            return {"error": f"YouTube Search Failed: {str(e)}"}

@register_node("youtube_video_details")
class YouTubeVideoDetailsNode(BaseNode):
    async def execute(self, input_data: Any, context: Optional[Dict[str, Any]] = None) -> Any:
        video_id = input_data if isinstance(input_data, str) else input_data.get("id", "")
        
        creds_data = await self.get_credential("credentials_id")
        api_key = creds_data.get("api_key") if creds_data else os.getenv("GOOGLE_API_KEY")
        
        if not api_key:
            return {"error": "YouTube/Google API Key is required."}

        try:
            youtube = build("youtube", "v3", developerKey=api_key)
            
            request = youtube.videos().list(
                part="snippet,statistics,contentDetails",
                id=video_id
            )
            response = request.execute()
            
            if not response.get("items"):
                return {"error": "Video not found"}
                
            item = response["items"][0]
            return {
                "title": item["snippet"]["title"],
                "channel": item["snippet"]["channelTitle"],
                "view_count": item["statistics"].get("viewCount"),
                "like_count": item["statistics"].get("likeCount"),
                "duration": item["contentDetails"]["duration"],
                "published_at": item["snippet"]["publishedAt"]
            }
        except Exception as e:
            return {"error": f"YouTube Video Details Failed: {str(e)}"}
