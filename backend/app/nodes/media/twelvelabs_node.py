"""
TwelveLabs Node - Studio Standard (Universal Method)
Batch 116: Specialized Toolkits
"""
from typing import Any, Dict, Optional, List
import aiohttp
import json
from ...base import BaseNode
from ...registry import register_node

@register_node("twelvelabs_node")
class TwelveLabsNode(BaseNode):
    """
    Video search and understanding using TwelveLabs.
    """
    node_type = "twelvelabs_node"
    version = "1.0.0"
    category = "media"
    credentials_required = ["twelvelabs_auth"]

    inputs = {
        "action": {
            "type": "dropdown",
            "default": "search",
            "options": ["search", "index_video", "generate_text"],
            "description": "TwelveLabs service to use"
        },
        "index_id": {
            "type": "string",
            "required": True,
            "description": "The ID of the video index"
        },
        "query": {
            "type": "string",
            "optional": True,
            "description": "Search query or question about the video"
        },
        "video_url": {
            "type": "string",
            "optional": True,
            "description": "URL of the video to index"
        }
    }

    outputs = {
        "result": {"type": "any"},
        "status": {"type": "string"}
    }

    async def execute(self, input_data: Any, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        try:
            creds = await self.get_credential("twelvelabs_auth")
            api_key = creds.get("api_key")
            
            if not api_key:
                return {"status": "error", "error": "TwelveLabs API Key is required"}

            action = self.get_config("action", "search")
            index_id = self.get_config("index_id")
            query = self.get_config("query") or str(input_data)

            base_url = "https://api.twelvelabs.io/v1.2"
            headers = {
                "x-api-key": api_key,
                "Content-Type": "application/json"
            }

            async with aiohttp.ClientSession() as session:
                if action == "search":
                    payload = {
                        "index_id": index_id,
                        "query": query,
                        "search_options": ["visual", "audio", "text"]
                    }
                    async with session.post(f"{base_url}/search", headers=headers, json=payload) as response:
                        data = await response.json()
                        return {"status": "success", "data": {"result": data.get("data", [])}}

                elif action == "generate_text":
                    # Generate text summary or answer
                    video_id = self.get_config("video_id") # assumed provided in input or config
                    payload = {
                        "video_id": video_id,
                        "prompt": query
                    }
                    async with session.post(f"{base_url}/generate", headers=headers, json=payload) as response:
                        data = await response.json()
                        return {"status": "success", "data": {"result": data}}

            return {"status": "error", "error": f"Action {action} not yet fully implemented for async node."}

        except Exception as e:
            return {"status": "error", "error": f"TwelveLabs failed: {str(e)}"}
