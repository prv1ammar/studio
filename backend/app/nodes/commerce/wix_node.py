"""
Wix Node - Studio Standard (Universal Method)
Batch 86: E-commerce Core
"""
from typing import Any, Dict, Optional, List
import aiohttp
from ..base import BaseNode
from ..registry import register_node

@register_node("wix_node")
class WixNode(BaseNode):
    """
    Manage Wix store data including Orders and Products via Wix REST API.
    """
    node_type = "wix_node"
    version = "1.0.0"
    category = "commerce"
    credentials_required = ["wix_auth"]


    properties = [
        {
            'displayName': 'Operation',
            'name': 'operation',
            'type': 'options',
            'default': 'query_orders',
            'options': [
                {'name': 'Query Orders', 'value': 'query_orders'},
                {'name': 'List Products', 'value': 'list_products'},
                {'name': 'Get Site Details', 'value': 'get_site_details'},
            ],
            'description': 'Wix action',
        },
        {
            'displayName': 'Site Id',
            'name': 'site_id',
            'type': 'string',
            'default': '',
            'description': 'Wix Site ID',
            'required': True,
        },
    ]
    inputs = {
        "action": {
            "type": "dropdown",
            "default": "query_orders",
            "options": ["query_orders", "list_products", "get_site_details"],
            "description": "Wix action"
        },
        "site_id": {
            "type": "string",
            "required": True,
            "description": "Wix Site ID"
        }
    }

    outputs = {
        "result": {"type": "any"},
        "status": {"type": "string"}
    }

    async def execute(self, input_data: Any, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        try:
            # 1. Authentication First
            creds = await self.get_credential("wix_auth")
            api_key = creds.get("api_key") if creds else self.get_config("api_key")
            
            if not api_key:
                return {"status": "error", "error": "Wix API Key is required."}

            headers = {
                "Authorization": api_key,
                "Content-Type": "application/json"
            }
            
            # 2. Connect to Real API
            site_id = self.get_config("site_id")
            base_url = "https://www.wixapis.com"
            action = self.get_config("action", "query_orders")

            async with aiohttp.ClientSession() as session:
                if action == "query_orders":
                    url = f"{base_url}/stores/v2/orders/query"
                    payload = {"query": {"paging": {"limit": 10}}}
                    async with session.post(url, headers=headers, json=payload) as resp:
                        if resp.status != 200:
                            return {"status": "error", "error": f"Wix Error: {resp.status}"}
                        res_data = await resp.json()
                        return {"status": "success", "data": {"result": res_data.get("orders", [])}}

                elif action == "list_products":
                    url = f"{base_url}/stores/v1/products/query"
                    payload = {"query": {"paging": {"limit": 10}}}
                    async with session.post(url, headers=headers, json=payload) as resp:
                        if resp.status != 200:
                            return {"status": "error", "error": f"Wix Error: {resp.status}"}
                        res_data = await resp.json()
                        return {"status": "success", "data": {"result": res_data.get("products", [])}}

                return {"status": "error", "error": f"Unsupported action: {action}"}

        except Exception as e:
            # 5. Error Handling
            return {"status": "error", "error": f"Wix Node Failed: {str(e)}"}