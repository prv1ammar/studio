"""
Zillow Node - Studio Standard
Batch 73: Real Estate & MLS
"""
from typing import Any, Dict, Optional, List
import aiohttp
from ..base import BaseNode
from ..registry import register_node

@register_node("zillow_node")
class ZillowNode(BaseNode):
    """
    Retrieve property valuations and listings via Zillow/RapidAPI.
    """
    node_type = "zillow_node"
    version = "1.0.0"
    category = "real_estate"
    credentials_required = ["zillow_auth"]


    properties = [
        {
            'displayName': 'Operation',
            'name': 'operation',
            'type': 'options',
            'default': 'search_properties',
            'options': [
                {'name': 'Search Properties', 'value': 'search_properties'},
                {'name': 'Get Property Details', 'value': 'get_property_details'},
                {'name': 'Get Zestimate', 'value': 'get_zestimate'},
            ],
            'description': 'Zillow action',
        },
        {
            'displayName': 'Location',
            'name': 'location',
            'type': 'string',
            'default': '',
            'description': 'Address or City, State',
        },
        {
            'displayName': 'Zpid',
            'name': 'zpid',
            'type': 'string',
            'default': '',
            'description': 'Zillow Property ID',
        },
    ]
    inputs = {
        "action": {
            "type": "dropdown",
            "default": "search_properties",
            "options": ["search_properties", "get_property_details", "get_zestimate"],
            "description": "Zillow action"
        },
        "location": {
            "type": "string",
            "optional": True,
            "description": "Address or City, State"
        },
        "zpid": {
            "type": "string",
            "optional": True,
            "description": "Zillow Property ID"
        }
    }

    outputs = {
        "result": {"type": "any"},
        "status": {"type": "string"}
    }

    async def execute(self, input_data: Any, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        try:
            creds = await self.get_credential("zillow_auth")
            api_key = creds.get("api_key") if creds else self.get_config("api_key")
            api_host = creds.get("api_host", "zillow-com1.p.rapidapi.com")
            
            if not api_key:
                return {"status": "error", "error": "RapidAPI Key (for Zillow) is required."}

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
                    url = f"{base_url}/propertyExtendedSearch"
                    params = {"location": location, "status_type": "ForSale"}
                    async with session.get(url, headers=headers, params=params) as resp:
                        res_data = await resp.json()
                        return {"status": "success", "data": {"result": res_data.get("props", [])}}

                elif action == "get_property_details":
                    zpid = self.get_config("zpid") or str(input_data)
                    url = f"{base_url}/property"
                    params = {"zpid": zpid}
                    async with session.get(url, headers=headers, params=params) as resp:
                        res_data = await resp.json()
                        return {"status": "success", "data": {"result": res_data}}

                return {"status": "error", "error": f"Unsupported action: {action}"}

        except Exception as e:
            return {"status": "error", "error": f"Zillow Node Failed: {str(e)}"}