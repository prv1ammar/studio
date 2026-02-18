"""
JigsawStack Node - Studio Standard (Universal Method)
Batch 116: Specialized Toolkits
"""
from typing import Any, Dict, Optional, List
import aiohttp
from ..base import BaseNode
from ..registry import register_node

@register_node("jigsawstack_node")
class JigsawStackNode(BaseNode):
    """
    Unified node for JigsawStack AI services (OCR, Scrape, Translate, etc.).
    """
    node_type = "jigsawstack_node"
    version = "1.0.0"
    category = "ai"
    credentials_required = ["jigsawstack_auth"]


    properties = [
        {
            'displayName': 'Operation',
            'name': 'operation',
            'type': 'options',
            'default': 'ai_scrape',
            'options': [
                {'name': 'Ai Scrape', 'value': 'ai_scrape'},
                {'name': 'Ai Web Search', 'value': 'ai_web_search'},
                {'name': 'Translate', 'value': 'translate'},
                {'name': 'Sentiment', 'value': 'sentiment'},
                {'name': 'Object Detection', 'value': 'object_detection'},
                {'name': 'Image Generation', 'value': 'image_generation'},
                {'name': 'Vocr', 'value': 'vocr'},
            ],
            'description': 'JigsawStack service to use',
        },
        {
            'displayName': 'Text',
            'name': 'text',
            'type': 'string',
            'default': '',
            'description': 'Text or URL for processing',
        },
        {
            'displayName': 'Url',
            'name': 'url',
            'type': 'string',
            'default': '',
            'description': 'URL for scraping or search',
        },
    ]
    inputs = {
        "action": {
            "type": "dropdown",
            "default": "ai_scrape",
            "options": [
                "ai_scrape", "ai_web_search", "translate", "sentiment", 
                "object_detection", "image_generation", "vocr"
            ],
            "description": "JigsawStack service to use"
        },
        "text": {
            "type": "string",
            "optional": True,
            "description": "Text or URL for processing"
        },
        "url": {
            "type": "string",
            "optional": True,
            "description": "URL for scraping or search"
        }
    }

    outputs = {
        "result": {"type": "any"},
        "status": {"type": "string"}
    }

    async def execute(self, input_data: Any, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        try:
            creds = await self.get_credential("jigsawstack_auth")
            api_key = creds.get("api_key")
            
            if not api_key:
                return {"status": "error", "error": "JigsawStack API Key is required"}

            action = self.get_config("action", "ai_scrape")
            text = self.get_config("text") or str(input_data)
            url_cfg = self.get_config("url")

            base_url = "https://api.jigsawstack.com/v1"
            headers = {
                "x-api-key": api_key,
                "Content-Type": "application/json"
            }

            async with aiohttp.ClientSession() as session:
                if action == "ai_scrape":
                    target = url_cfg or text
                    payload = {"url": target}
                    async with session.post(f"{base_url}/ai/scrape", headers=headers, json=payload) as response:
                        data = await response.json()
                        return {"status": "success", "data": {"result": data}}

                elif action == "ai_web_search":
                    payload = {"query": text}
                    async with session.get(f"{base_url}/ai/search", headers=headers, params=payload) as response:
                        data = await response.json()
                        return {"status": "success", "data": {"result": data}}

                elif action == "translate":
                    payload = {"text": text, "target_language": "en"}
                    async with session.post(f"{base_url}/ai/translate", headers=headers, json=payload) as response:
                        data = await response.json()
                        return {"status": "success", "data": {"result": data}}

                elif action == "sentiment":
                    payload = {"text": text}
                    async with session.post(f"{base_url}/ai/sentiment", headers=headers, json=payload) as response:
                        data = await response.json()
                        return {"status": "success", "data": {"result": data}}

            return {"status": "error", "error": f"Action {action} not yet implemented in this node."}

        except Exception as e:
            return {"status": "error", "error": f"JigsawStack failed: {str(e)}"}