"""
Expedia Node - Studio Standard
Batch 72: Travel & Hospitality
"""
from typing import Any, Dict, Optional, List
import aiohttp
from ..base import BaseNode
from ..registry import register_node

@register_node("expedia_node")
class ExpediaNode(BaseNode):
    """
    Access global travel inventories via the Expedia Rapid API.
    """
    node_type = "expedia_node"
    version = "1.0.0"
    category = "travel"
    credentials_required = ["expedia_auth"]


    properties = [
        {
            'displayName': 'Operation',
            'name': 'operation',
            'type': 'options',
            'default': 'search_properties',
            'options': [
                {'name': 'Search Properties', 'value': 'search_properties'},
                {'name': 'Get Property Details', 'value': 'get_property_details'},
                {'name': 'List Regions', 'value': 'list_regions'},
            ],
            'description': 'Expedia action',
        },
        {
            'displayName': 'Property Id',
            'name': 'property_id',
            'type': 'string',
            'default': '',
        },
        {
            'displayName': 'Region Id',
            'name': 'region_id',
            'type': 'string',
            'default': '',
            'description': 'ID of the region (e.g. city or neighborhood)',
        },
    ]
    inputs = {
        "action": {
            "type": "dropdown",
            "default": "search_properties",
            "options": ["search_properties", "get_property_details", "list_regions"],
            "description": "Expedia action"
        },
        "region_id": {
            "type": "string",
            "optional": True,
            "description": "ID of the region (e.g. city or neighborhood)"
        },
        "property_id": {
            "type": "string",
            "optional": True
        }
    }

    outputs = {
        "result": {"type": "any"},
        "status": {"type": "string"},
        "count": {"type": "number"}
    }

    async def execute(self, input_data: Any, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        try:
            creds = await self.get_credential("expedia_auth")
            api_key = creds.get("api_key") if creds else self.get_config("api_key")
            api_secret = creds.get("api_secret") if creds else self.get_config("api_secret")
            
            if not api_key:
                return {"status": "error", "error": "Expedia API Key is required."}

            headers = {
                "Authorization": f"Basic {api_key}:{api_secret}", # Usually API Key based
                "Accept": "application/json"
            }
            
            # Note: Expedia Rapid uses different endpoints for search vs content
            base_url = "https://test.api.ean.com/v3" # Rapid API Test Endpoint
            action = self.get_config("action", "search_properties")

            async with aiohttp.ClientSession() as session:
                if action == "list_regions":
                    url = f"{base_url}/regions"
                    async with session.get(url, headers=headers) as resp:
                        res_data = await resp.json()
                        return {"status": "success", "data": {"result": res_data.get("data", [])}}

                elif action == "search_properties":
                    url = f"{base_url}/properties/availability"
                    params = {
                        "checkin": "2024-12-01",
                        "checkout": "2024-12-05",
                        "region_id": self.get_config("region_id") or "2621"
                    }
                    async with session.get(url, headers=headers, params=params) as resp:
                        res_data = await resp.json()
                        properties = res_data.get("data", [])
                        return {"status": "success", "data": {"result": properties, "count": len(properties)}}

                return {"status": "error", "error": f"Unsupported action: {action}"}

        except Exception as e:
            return {"status": "error", "error": f"Expedia Node Failed: {str(e)}"}