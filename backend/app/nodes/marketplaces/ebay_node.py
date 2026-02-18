"""
eBay Node - Studio Standard (Universal Method)
Batch 87: Retail & Marketplaces
"""
from typing import Any, Dict, Optional, List
import aiohttp
from ..base import BaseNode
from ..registry import register_node

@register_node("ebay_node")
class EbayNode(BaseNode):
    """
    Orchestrate eBay listings and transactions via the eBay REST API.
    """
    node_type = "ebay_node"
    version = "1.0.0"
    category = "marketplaces"
    credentials_required = ["ebay_auth"]


    properties = [
        {
            'displayName': 'Operation',
            'name': 'operation',
            'type': 'options',
            'default': 'get_orders',
            'options': [
                {'name': 'Get Orders', 'value': 'get_orders'},
                {'name': 'Search Listings', 'value': 'search_listings'},
                {'name': 'Get Account Details', 'value': 'get_account_details'},
            ],
            'description': 'eBay action',
        },
    ]
    inputs = {
        "action": {
            "type": "dropdown",
            "default": "get_orders",
            "options": ["get_orders", "search_listings", "get_account_details"],
            "description": "eBay action"
        }
    }

    outputs = {
        "result": {"type": "any"},
        "status": {"type": "string"}
    }

    async def execute(self, input_data: Any, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        try:
            # 1. Authentication (OAuth 2.0 User Token)
            creds = await self.get_credential("ebay_auth")
            access_token = creds.get("access_token")
            
            if not access_token:
                return {"status": "error", "error": "eBay User Access Token required."}

            headers = {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json",
                "Accept": "application/json"
            }
            
            # 2. Connect to Real API
            base_url = "https://api.ebay.com/sell/fulfillment/v1"
            action = self.get_config("action", "get_orders")

            async with aiohttp.ClientSession() as session:
                if action == "get_orders":
                    url = f"{base_url}/order"
                    async with session.get(url, headers=headers) as resp:
                        if resp.status != 200:
                            return {"status": "error", "error": f"eBay Error: {resp.status} - {await resp.text()}"}
                        res_data = await resp.json()
                        return {"status": "success", "data": {"result": res_data.get("orders", [])}}

                elif action == "search_listings":
                    # Using Browse API for searching
                    url = "https://api.ebay.com/buy/browse/v1/item_summary/search"
                    q = str(input_data)
                    params = {"q": q, "limit": 10}
                    async with session.get(url, headers=headers, params=params) as resp:
                        res_data = await resp.json()
                        return {"status": "success", "data": {"result": res_data.get("itemSummaries", [])}}

                return {"status": "error", "error": f"Unsupported action: {action}"}

        except Exception as e:
            return {"status": "error", "error": f"eBay Node Failed: {str(e)}"}