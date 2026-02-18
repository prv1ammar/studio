"""
Etsy Node - Studio Standard (Universal Method)
Batch 87: Retail & Marketplaces
"""
from typing import Any, Dict, Optional, List
import aiohttp
from ..base import BaseNode
from ..registry import register_node

@register_node("etsy_node")
class EtsyNode(BaseNode):
    """
    Manage Etsy shop listings, receipts, and shop data via Etsy API v3.
    """
    node_type = "etsy_node"
    version = "1.0.0"
    category = "marketplaces"
    credentials_required = ["etsy_auth"]


    properties = [
        {
            'displayName': 'Operation',
            'name': 'operation',
            'type': 'options',
            'default': 'get_shop_receipts',
            'options': [
                {'name': 'Get Shop Receipts', 'value': 'get_shop_receipts'},
                {'name': 'List Listings By Shop', 'value': 'list_listings_by_shop'},
                {'name': 'Get Shop Details', 'value': 'get_shop_details'},
            ],
            'description': 'Etsy API action',
        },
        {
            'displayName': 'Shop Id',
            'name': 'shop_id',
            'type': 'string',
            'default': '',
            'description': 'Unique ID of your Etsy shop',
            'required': True,
        },
    ]
    inputs = {
        "action": {
            "type": "dropdown",
            "default": "get_shop_receipts",
            "options": ["get_shop_receipts", "list_listings_by_shop", "get_shop_details"],
            "description": "Etsy API action"
        },
        "shop_id": {
            "type": "string",
            "required": True,
            "description": "Unique ID of your Etsy shop"
        }
    }

    outputs = {
        "result": {"type": "any"},
        "status": {"type": "string"}
    }

    async def execute(self, input_data: Any, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        try:
            # 1. Authentication (OAuth 2.0)
            creds = await self.get_credential("etsy_auth")
            access_token = creds.get("access_token")
            api_key = creds.get("api_key") # keystring
            
            if not access_token or not api_key:
                return {"status": "error", "error": "Etsy Access Token and API Key required."}

            headers = {
                "x-api-key": api_key,
                "Authorization": f"Bearer {access_token}",
                "Accept": "application/json"
            }
            
            # 2. Connect to Real API
            base_url = "https://openapi.etsy.com/v3/application"
            action = self.get_config("action", "get_shop_receipts")
            shop_id = self.get_config("shop_id")

            async with aiohttp.ClientSession() as session:
                if action == "get_shop_receipts":
                    url = f"{base_url}/shops/{shop_id}/receipts"
                    async with session.get(url, headers=headers) as resp:
                        if resp.status != 200:
                            return {"status": "error", "error": f"Etsy Error: {resp.status} - {await resp.text()}"}
                        res_data = await resp.json()
                        return {"status": "success", "data": {"result": res_data.get("results", [])}}

                elif action == "list_listings_by_shop":
                    url = f"{base_url}/shops/{shop_id}/listings/active"
                    async with session.get(url, headers=headers) as resp:
                        if resp.status != 200:
                            return {"status": "error", "error": f"Etsy Error: {resp.status}"}
                        res_data = await resp.json()
                        return {"status": "success", "data": {"result": res_data.get("results", [])}}

                return {"status": "error", "error": f"Unsupported action: {action}"}

        except Exception as e:
            # 5. Error Handling
            return {"status": "error", "error": f"Etsy Node Failed: {str(e)}"}