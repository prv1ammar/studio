"""
Zomato Node - Studio Standard
Batch 80: Industrial & Service Ops
"""
from typing import Any, Dict, Optional, List
import aiohttp
from ..base import BaseNode
from ..registry import register_node

@register_node("zomato_node")
class ZomatoNode(BaseNode):
    """
    Search restaurants and reviews via Zomato/Zomato API.
    """
    node_type = "zomato_node"
    version = "1.0.0"
    category = "food_delivery"
    credentials_required = ["zomato_auth"]


    properties = [
        {
            'displayName': 'Operation',
            'name': 'operation',
            'type': 'options',
            'default': 'search_restaurants',
            'options': [
                {'name': 'Search Restaurants', 'value': 'search_restaurants'},
                {'name': 'Get Reviews', 'value': 'get_reviews'},
                {'name': 'Get Daily Menu', 'value': 'get_daily_menu'},
            ],
            'description': 'Zomato action',
        },
        {
            'displayName': 'Query',
            'name': 'query',
            'type': 'string',
            'default': '',
        },
    ]
    inputs = {
        "action": {
            "type": "dropdown",
            "default": "search_restaurants",
            "options": ["search_restaurants", "get_reviews", "get_daily_menu"],
            "description": "Zomato action"
        },
        "query": {
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
            creds = await self.get_credential("zomato_auth")
            api_key = creds.get("user_key") or creds.get("api_key")
            
            if not api_key:
                 return {"status": "error", "error": "Zomato User Key is required."}

            headers = {"user-key": api_key, "Accept": "application/json"}
            base_url = "https://developers.zomato.com/api/v2.1"
            action = self.get_config("action", "search_restaurants")

            async with aiohttp.ClientSession() as session:
                if action == "search_restaurants":
                    q = self.get_config("query") or str(input_data)
                    url = f"{base_url}/search"
                    params = {"q": q}
                    async with session.get(url, headers=headers, params=params) as resp:
                        res_data = await resp.json()
                        return {"status": "success", "data": {"result": res_data.get("restaurants", [])}}
                
                return {"status": "error", "error": f"Unsupported action: {action}"}
        except Exception as e:
            return {"status": "error", "error": f"Zomato Node Failed: {str(e)}"}