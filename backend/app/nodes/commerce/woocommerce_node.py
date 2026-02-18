"""
WooCommerce Node - Studio Standard (Universal Method)
Batch 102: E-commerce & Payments Expansion
"""
from typing import Any, Dict, Optional, List
import aiohttp
import base64
from ..base import BaseNode
from ..registry import register_node

@register_node("woocommerce_node")
class WooCommerceNode(BaseNode):
    """
    WordPress e-commerce integration via WooCommerce REST API.
    """
    node_type = "woocommerce_node"
    version = "1.0.0"
    category = "commerce"
    credentials_required = ["woocommerce_auth"]


    properties = [
        {
            'displayName': 'Operation',
            'name': 'operation',
            'type': 'options',
            'default': 'list_products',
            'options': [
                {'name': 'List Products', 'value': 'list_products'},
                {'name': 'Create Product', 'value': 'create_product'},
                {'name': 'Update Product', 'value': 'update_product'},
                {'name': 'List Orders', 'value': 'list_orders'},
                {'name': 'Update Order Status', 'value': 'update_order_status'},
                {'name': 'Get Customer', 'value': 'get_customer'},
            ],
            'description': 'WooCommerce action',
        },
        {
            'displayName': 'Name',
            'name': 'name',
            'type': 'string',
            'default': '',
        },
        {
            'displayName': 'Order Id',
            'name': 'order_id',
            'type': 'string',
            'default': '',
        },
        {
            'displayName': 'Price',
            'name': 'price',
            'type': 'string',
            'default': '',
        },
        {
            'displayName': 'Product Id',
            'name': 'product_id',
            'type': 'string',
            'default': '',
        },
        {
            'displayName': 'Status',
            'name': 'status',
            'type': 'options',
            'default': '',
            'options': [
                {'name': 'Pending', 'value': 'pending'},
                {'name': 'Processing', 'value': 'processing'},
                {'name': 'On-Hold', 'value': 'on-hold'},
                {'name': 'Completed', 'value': 'completed'},
                {'name': 'Cancelled', 'value': 'cancelled'},
                {'name': 'Refunded', 'value': 'refunded'},
                {'name': 'Failed', 'value': 'failed'},
            ],
        },
    ]
    inputs = {
        "action": {
            "type": "dropdown",
            "default": "list_products",
            "options": ["list_products", "create_product", "update_product", "list_orders", "update_order_status", "get_customer"],
            "description": "WooCommerce action"
        },
        "product_id": {
            "type": "string",
            "optional": True
        },
        "order_id": {
            "type": "string",
            "optional": True
        },
        "name": {
            "type": "string",
            "optional": True
        },
        "price": {
            "type": "string",
            "optional": True
        },
        "status": {
            "type": "dropdown",
            "options": ["pending", "processing", "on-hold", "completed", "cancelled", "refunded", "failed"],
            "optional": True
        }
    }

    outputs = {
        "result": {"type": "any"},
        "status": {"type": "string"}
    }

    async def execute(self, input_data: Any, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        try:
            # 1. Authentication
            creds = await self.get_credential("woocommerce_auth")
            store_url = creds.get("store_url")  # e.g., "https://mystore.com"
            consumer_key = creds.get("consumer_key")
            consumer_secret = creds.get("consumer_secret")
            
            if not all([store_url, consumer_key, consumer_secret]):
                return {"status": "error", "error": "WooCommerce Store URL, Consumer Key, and Consumer Secret required."}

            # 2. Connect to Real API
            base_url = f"{store_url.rstrip('/')}/wp-json/wc/v3"
            
            # WooCommerce uses Basic Auth with consumer key:secret
            auth_str = f"{consumer_key}:{consumer_secret}"
            b64_auth = base64.b64encode(auth_str.encode()).decode()
            
            headers = {
                "Authorization": f"Basic {b64_auth}",
                "Content-Type": "application/json"
            }
            
            action = self.get_config("action", "list_products")

            async with aiohttp.ClientSession() as session:
                if action == "list_products":
                    url = f"{base_url}/products"
                    async with session.get(url, headers=headers) as resp:
                        if resp.status != 200:
                            error_text = await resp.text()
                            return {"status": "error", "error": f"WooCommerce API Error {resp.status}: {error_text}"}
                        res_data = await resp.json()
                        return {"status": "success", "data": {"result": res_data}}

                elif action == "create_product":
                    name = self.get_config("name")
                    price = self.get_config("price", "0.00")
                    
                    if not name:
                        return {"status": "error", "error": "name required"}
                    
                    url = f"{base_url}/products"
                    payload = {
                        "name": name,
                        "type": "simple",
                        "regular_price": price,
                        "status": "publish"
                    }
                    async with session.post(url, headers=headers, json=payload) as resp:
                        if resp.status not in [200, 201]:
                            error_text = await resp.text()
                            return {"status": "error", "error": f"WooCommerce API Error {resp.status}: {error_text}"}
                        res_data = await resp.json()
                        return {"status": "success", "data": {"result": res_data}}

                elif action == "update_product":
                    product_id = self.get_config("product_id")
                    if not product_id:
                        return {"status": "error", "error": "product_id required"}
                    
                    url = f"{base_url}/products/{product_id}"
                    payload = {}
                    
                    if self.get_config("name"):
                        payload["name"] = self.get_config("name")
                    if self.get_config("price"):
                        payload["regular_price"] = self.get_config("price")
                    
                    if not payload:
                        return {"status": "error", "error": "No update fields provided"}
                    
                    async with session.put(url, headers=headers, json=payload) as resp:
                        if resp.status != 200:
                            error_text = await resp.text()
                            return {"status": "error", "error": f"WooCommerce API Error {resp.status}: {error_text}"}
                        res_data = await resp.json()
                        return {"status": "success", "data": {"result": res_data}}

                elif action == "list_orders":
                    url = f"{base_url}/orders"
                    async with session.get(url, headers=headers) as resp:
                        if resp.status != 200:
                            error_text = await resp.text()
                            return {"status": "error", "error": f"WooCommerce API Error {resp.status}: {error_text}"}
                        res_data = await resp.json()
                        return {"status": "success", "data": {"result": res_data}}

                elif action == "update_order_status":
                    order_id = self.get_config("order_id")
                    status = self.get_config("status")
                    
                    if not order_id or not status:
                        return {"status": "error", "error": "order_id and status required"}
                    
                    url = f"{base_url}/orders/{order_id}"
                    payload = {"status": status}
                    
                    async with session.put(url, headers=headers, json=payload) as resp:
                        if resp.status != 200:
                            error_text = await resp.text()
                            return {"status": "error", "error": f"WooCommerce API Error {resp.status}: {error_text}"}
                        res_data = await resp.json()
                        return {"status": "success", "data": {"result": res_data}}

                elif action == "get_customer":
                    customer_id = str(input_data) if input_data else self.get_config("product_id")
                    url = f"{base_url}/customers/{customer_id}"
                    async with session.get(url, headers=headers) as resp:
                        if resp.status != 200:
                            error_text = await resp.text()
                            return {"status": "error", "error": f"WooCommerce API Error {resp.status}: {error_text}"}
                        res_data = await resp.json()
                        return {"status": "success", "data": {"result": res_data}}

                return {"status": "error", "error": f"Unsupported action: {action}"}

        except Exception as e:
            return {"status": "error", "error": f"WooCommerce Node Failed: {str(e)}"}