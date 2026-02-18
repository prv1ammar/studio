"""
Amazon SP-API Node - Studio Standard (Universal Method)
Batch 87: Retail & Marketplaces
"""
from typing import Any, Dict, Optional, List
import aiohttp
from ..base import BaseNode
from ..registry import register_node

@register_node("amazon_sp_node")
class AmazonSPNode(BaseNode):
    """
    Access Selling Partner (SP) metrics, orders, and fulfillment data via Amazon SP-API.
    """
    node_type = "amazon_sp_node"
    version = "1.0.0"
    category = "marketplaces"
    credentials_required = ["amazon_sp_auth"]


    properties = [
        {
            'displayName': 'Operation',
            'name': 'operation',
            'type': 'options',
            'default': 'get_orders',
            'options': [
                {'name': 'Get Orders', 'value': 'get_orders'},
                {'name': 'Get Catalog Item', 'value': 'get_catalog_item'},
                {'name': 'List Financial Events', 'value': 'list_financial_events'},
                {'name': 'Get Marketplace Participations', 'value': 'get_marketplace_participations'},
            ],
            'description': 'Amazon SP-API action',
        },
        {
            'displayName': 'Marketplace Id',
            'name': 'marketplace_id',
            'type': 'string',
            'default': 'ATVPDKIKX0DER',
            'description': 'Amazon Marketplace ID',
        },
    ]
    inputs = {
        "action": {
            "type": "dropdown",
            "default": "get_orders",
            "options": ["get_orders", "get_catalog_item", "list_financial_events", "get_marketplace_participations"],
            "description": "Amazon SP-API action"
        },
        "marketplace_id": {
            "type": "string",
            "default": "ATVPDKIKX0DER", # Amazon.com
            "description": "Amazon Marketplace ID"
        }
    }

    outputs = {
        "result": {"type": "any"},
        "status": {"type": "string"}
    }

    async def execute(self, input_data: Any, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        try:
            # 1. Authentication (LWA - Login with Amazon)
            creds = await self.get_credential("amazon_sp_auth")
            access_token = creds.get("access_token") # Needs to be refreshed usually
            
            if not access_token:
                return {"status": "error", "error": "Amazon SP-API Access Token required."}

            headers = {
                "x-amz-access-token": access_token,
                "Content-Type": "application/json"
            }
            
            # 2. Connect to Real API
            # Region-specific endpoints (NA: https://sellingpartnerapi-na.amazon.com)
            region = creds.get("region", "na").lower()
            endpoints = {
                "na": "https://sellingpartnerapi-na.amazon.com",
                "eu": "https://sellingpartnerapi-eu.amazon.com",
                "fe": "https://sellingpartnerapi-fe.amazon.com"
            }
            base_url = endpoints.get(region, endpoints["na"])
            action = self.get_config("action", "get_orders")
            mkt_id = self.get_config("marketplace_id")

            async with aiohttp.ClientSession() as session:
                if action == "get_orders":
                    url = f"{base_url}/orders/v0/orders"
                    params = {"MarketplaceIds": mkt_id, "CreatedAfter": "2023-01-01"}
                    async with session.get(url, headers=headers, params=params) as resp:
                        if resp.status != 200:
                            return {"status": "error", "error": f"Amazon SP-API Error: {resp.status} - {await resp.text()}"}
                        res_data = await resp.json()
                        return {"status": "success", "data": {"result": res_data.get("payload", {}).get("Orders", [])}}

                elif action == "get_marketplace_participations":
                    url = f"{base_url}/sellers/v1/marketplaceParticipations"
                    async with session.get(url, headers=headers) as resp:
                        res_data = await resp.json()
                        return {"status": "success", "data": {"result": res_data.get("payload", [])}}

                return {"status": "error", "error": f"Unsupported action: {action}"}

        except Exception as e:
            # 5. Error Handling
            return {"status": "error", "error": f"Amazon SP-API Node Failed: {str(e)}"}