"""
Yelp Node - Studio Standard
Batch 81: Leisure, Health & Education
"""
from typing import Any, Dict, Optional, List
import aiohttp
from ..base import BaseNode
from ..registry import register_node

@register_node("yelp_node")
class YelpNode(BaseNode):
    """
    Search businesses and reviews via the Yelp Fusion API.
    """
    node_type = "yelp_node"
    version = "1.0.0"
    category = "leisure"
    credentials_required = ["yelp_auth"]


    properties = [
        {
            'displayName': 'Operation',
            'name': 'operation',
            'type': 'options',
            'default': 'search_business',
            'options': [
                {'name': 'Search Business', 'value': 'search_business'},
                {'name': 'Get Reviews', 'value': 'get_reviews'},
                {'name': 'Get Business Details', 'value': 'get_business_details'},
            ],
            'description': 'Yelp action',
        },
        {
            'displayName': 'Location',
            'name': 'location',
            'type': 'string',
            'default': '',
        },
        {
            'displayName': 'Term',
            'name': 'term',
            'type': 'string',
            'default': '',
        },
    ]
    inputs = {
        "action": {
            "type": "dropdown",
            "default": "search_business",
            "options": ["search_business", "get_reviews", "get_business_details"],
            "description": "Yelp action"
        },
        "location": {
            "type": "string",
            "optional": True
        },
        "term": {
            "type": "string",
            "optional": True
        }
    }

    async def execute(self, input_data: Any, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        try:
            creds = await self.get_credential("yelp_auth")
            api_key = creds.get("api_key")
            headers = {"Authorization": f"Bearer {api_key}"}
            base_url = "https://api.yelp.com/v3"
            
            async with aiohttp.ClientSession() as session:
                url = f"{base_url}/businesses/search"
                params = {"location": self.get_config("location", "NYC"), "term": self.get_config("term", "food")}
                async with session.get(url, headers=headers, params=params) as resp:
                    res_data = await resp.json()
                    return {"status": "success", "data": {"result": res_data}}
        except Exception as e:
            return {"status": "error", "error": str(e)}