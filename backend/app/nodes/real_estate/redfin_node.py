"""
Redfin Node - Studio Standard
Batch 73: Real Estate & MLS
"""
from typing import Any, Dict, Optional, List
import aiohttp
from ..base import BaseNode
from ..registry import register_node

@register_node("redfin_node")
class RedfinNode(BaseNode):
    """
    Retrieve market data and property listings via Redfin/RapidAPI.
    """
    node_type = "redfin_node"
    version = "1.0.0"
    category = "real_estate"
    credentials_required = ["redfin_auth"]


    properties = [
        {
            'displayName': 'Operation',
            'name': 'operation',
            'type': 'options',
            'default': 'search_properties',
            'options': [
                {'name': 'Search Properties', 'value': 'search_properties'},
                {'name': 'Get Property Details', 'value': 'get_property_details'},
                {'name': 'Get Market Stats', 'value': 'get_market_stats'},
            ],
            'description': 'Redfin action',
        },
        {
            'displayName': 'Location',
            'name': 'location',
            'type': 'string',
            'default': '',
            'description': 'City, State or Zip',
        },
        {
            'displayName': 'Property Id',
            'name': 'property_id',
            'type': 'string',
            'default': '',
        },
    ]
    inputs = {
        "action": {
            "type": "dropdown",
            "default": "search_properties",
            "options": ["search_properties", "get_property_details", "get_market_stats"],
            "description": "Redfin action"
        },
        "location": {
            "type": "string",
            "optional": True,
            "description": "City, State or Zip"
        },
        "property_id": {
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
            creds = await self.get_credential("redfin_auth")
            api_key = creds.get("api_key") if creds else self.get_config("api_key")
            api_host = creds.get("api_host", "redfin-com-data.p.rapidapi.com")
            
            if not api_key:
                return {"status": "error", "error": "RapidAPI Key (for Redfin) is required."}

            headers = {
                "X-RapidAPI-Key": api_key,
                "X-RapidAPI-Host": api_host,
                "Accept": "application/json"
            }
            
            base_url = f"https://{api_host}"
            action = self.get_config("action", "search_properties")

            async with aiohttp.ClientSession() as session:
                if action == "search_properties":
                    location = self.get_config("location") or str(input_data)
                    url = f"{base_url}/properties/search"
                    params = {"location": location}
                    async with session.get(url, headers=headers, params=params) as resp:
                        res_data = await resp.json()
                        return {"status": "success", "data": {"result": res_data}}

                elif action == "get_property_details":
                    p_id = self.get_config("property_id") or str(input_data)
                    url = f"{base_url}/properties/detail"
                    params = {"property_id": p_id}
                    async with session.get(url, headers=headers, params=params) as resp:
                        res_data = await resp.json()
                        return {"status": "success", "data": {"result": res_data}}

                return {"status": "error", "error": f"Unsupported action: {action}"}

        except Exception as e:
            return {"status": "error", "error": f"Redfin Node Failed: {str(e)}"}