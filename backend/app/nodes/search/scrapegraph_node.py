"""
ScrapeGraph Node - Studio Standard (Universal Method)
Batch 117: Advanced Document Processing
"""
from typing import Any, Dict, Optional, List
import aiohttp
from ..base import BaseNode
from ..registry import register_node

@register_node("scrapegraph_node")
class ScrapeGraphNode(BaseNode):
    """
    Intelligent web scraping using LLM-powered ScrapeGraphAI.
    """
    node_type = "scrapegraph_node"
    version = "1.0.0"
    category = "search"
    credentials_required = ["scrapegraph_auth"]


    properties = [
        {
            'displayName': 'Operation',
            'name': 'operation',
            'type': 'options',
            'default': 'smart_scraper',
            'options': [
                {'name': 'Smart Scraper', 'value': 'smart_scraper'},
                {'name': 'Search', 'value': 'search'},
                {'name': 'Markdownify', 'value': 'markdownify'},
            ],
            'description': 'ScrapeGraphAI service to use',
        },
        {
            'displayName': 'Prompt',
            'name': 'prompt',
            'type': 'string',
            'default': '',
            'description': 'What data should be extracted? (e.g. 'Extract all product names and prices')',
            'required': True,
        },
        {
            'displayName': 'Url',
            'name': 'url',
            'type': 'string',
            'default': '',
            'description': 'The URL to scrape or search',
            'required': True,
        },
    ]
    inputs = {
        "action": {
            "type": "dropdown",
            "default": "smart_scraper",
            "options": ["smart_scraper", "search", "markdownify"],
            "description": "ScrapeGraphAI service to use"
        },
        "url": {
            "type": "string",
            "required": True,
            "description": "The URL to scrape or search"
        },
        "prompt": {
            "type": "string",
            "required": True,
            "description": "What data should be extracted? (e.g. 'Extract all product names and prices')"
        }
    }

    outputs = {
        "result": {"type": "any"},
        "status": {"type": "string"}
    }

    async def execute(self, input_data: Any, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        try:
            creds = await self.get_credential("scrapegraph_auth")
            api_key = creds.get("api_key")
            
            if not api_key:
                return {"status": "error", "error": "ScrapeGraph API Key is required"}

            action = self.get_config("action", "smart_scraper")
            url = self.get_config("url") or str(input_data)
            prompt = self.get_config("prompt")

            # Using ScrapeGraph REST API
            base_url = "https://api.scrapegraphai.com/v1"
            headers = {
                "SGRP-API-KEY": api_key,
                "Content-Type": "application/json"
            }
            
            endpoint = "/smartscraper"
            payload = {
                "website_url": url,
                "user_prompt": prompt
            }
            
            if action == "search":
                endpoint = "/search"
                payload = {"user_prompt": prompt}
            elif action == "markdownify":
                endpoint = "/markdownify"
                payload = {"website_url": url}

            async with aiohttp.ClientSession() as session:
                async with session.post(f"{base_url}{endpoint}", headers=headers, json=payload) as response:
                    if response.status != 200:
                        text = await response.text()
                        return {"status": "error", "error": f"ScrapeGraph error {response.status}: {text}"}
                    
                    data = await response.json()

            return {
                "status": "success",
                "data": {
                    "result": data
                }
            }

        except Exception as e:
            return {"status": "error", "error": f"ScrapeGraph failed: {str(e)}"}