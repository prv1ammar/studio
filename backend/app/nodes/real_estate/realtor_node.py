"""
Realtor Node - Studio Standard
Batch 73: Real Estate & MLS
"""
from typing import Any, Dict, Optional, List
import aiohttp
from ..base import BaseNode
from ..registry import register_node

@register_node("realtor_node")
class RealtorNode(BaseNode):
    """
    Access official MLS listings and property data via Realtor.com/RapidAPI.
    """
    node_type = "realtor_node"
    version = "1.0.0"
    category = "real_estate"
    credentials_required = ["realtor_auth"]


    properties = [
        {
            'displayName': 'Operation',
            'name': 'operation',
            'type': 'options',
            'default': 'list_for_sale',
            'options': [
                {'name': 'List For Sale', 'value': 'list_for_sale'},
                {'name': 'List For Rent', 'value': 'list_for_rent'},
                {'name': 'Get Property Detail', 'value': 'get_property_detail'},
            ],
            'description': 'Realtor.com action',
        },
        {
            'displayName': 'City',
            'name': 'city',
            'type': 'string',
            'default': '',
        },
        {
            'displayName': 'Property Id',
            'name': 'property_id',
            'type': 'string',
            'default': '',
        },
        {
            'displayName': 'State Code',
            'name': 'state_code',
            'type': 'string',
            'default': '',
            'description': 'Two-letter state code (e.g. CA, NY)',
        },
    ]
    inputs = {
        "action": {
            "type": "dropdown",
            "default": "list_for_sale",
            "options": ["list_for_sale", "list_for_rent", "get_property_detail"],
            "description": "Realtor.com action"
        },
        "city": {
            "type": "string",
            "optional": True
        },
        "state_code": {
            "type": "string",
            "optional": True,
            "description": "Two-letter state code (e.g. CA, NY)"
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
            creds = await self.get_credential("realtor_auth")
            api_key = creds.get("api_key") if creds else self.get_config("api_key")
            api_host = creds.get("api_host", "realtor.p.rapidapi.com")
            
            if not api_key:
                return {"status": "error", "error": "RapidAPI Key (for Realtor.com) is required."}

            headers = {
                "X-RapidAPI-Key": api_key,
                "X-RapidAPI-Host": api_host,
                "Accept": "application/json"
            }
            
            base_url = f"https://{api_host}"
            action = self.get_config("action", "list_for_sale")

            async with aiohttp.ClientSession() as session:
                if action == "list_for_sale":
                    city = self.get_config("city") or "New York City"
                    state = self.get_config("state_code") or "NY"
                    url = f"{base_url}/properties/v2/list-for-sale"
                    params = {"city": city, "state_code": state, "limit": 10, "offset": 0}
                    async with session.get(url, headers=headers, params=params) as resp:
                        res_data = await resp.json()
                        return {"status": "success", "data": {"result": res_data.get("properties", [])}}

                elif action == "get_property_detail":
                    p_id = self.get_config("property_id") or str(input_data)
                    url = f"{base_url}/properties/v2/detail"
                    params = {"property_id": p_id}
                    async with session.get(url, headers=headers, params=params) as resp:
                        res_data = await resp.json()
                        return {"status": "success", "data": {"result": res_data}}

                return {"status": "error", "error": f"Unsupported action: {action}"}

        except Exception as e:
            return {"status": "error", "error": f"Realtor Node Failed: {str(e)}"}