"""
Shopify Node - Studio Standard (Universal Method)
Batch 102: E-commerce & Payments Expansion
"""
from typing import Any, Dict, Optional, List
import aiohttp
from ..base import BaseNode
from ..registry import register_node

@register_node("shopify_node")
class ShopifyNode(BaseNode):
    """
    Complete Shopify store management via Admin API.
    """
    node_type = "shopify_node"
    version = "1.0.0"
    category = "commerce"
    credentials_required = ["shopify_auth"]


    properties = [
        {
            'displayName': 'Operation',
            'name': 'operation',
            'type': 'options',
            'default': 'list_products',
            'options': [
                {'name': 'List Products', 'value': 'list_products'},
                {'name': 'Create Product', 'value': 'create_product'},
                {'name': 'Update Inventory', 'value': 'update_inventory'},
                {'name': 'List Orders', 'value': 'list_orders'},
                {'name': 'Create Order', 'value': 'create_order'},
                {'name': 'Get Customer', 'value': 'get_customer'},
            ],
            'description': 'Shopify action',
        },
        {
            'displayName': 'Customer Email',
            'name': 'customer_email',
            'type': 'string',
            'default': '',
        },
        {
            'displayName': 'Inventory Quantity',
            'name': 'inventory_quantity',
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
            'displayName': 'Title',
            'name': 'title',
            'type': 'string',
            'default': '',
        },
    ]
    inputs = {
        "action": {
            "type": "dropdown",
            "default": "list_products",
            "options": ["list_products", "create_product", "update_inventory", "list_orders", "create_order", "get_customer"],
            "description": "Shopify action"
        },
        "product_id": {
            "type": "string",
            "optional": True
        },
        "title": {
            "type": "string",
            "optional": True
        },
        "price": {
            "type": "string",
            "optional": True
        },
        "inventory_quantity": {
            "type": "string",
            "optional": True
        },
        "customer_email": {
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
            # 1. Authentication
            creds = await self.get_credential("shopify_auth")
            shop_domain = creds.get("shop_domain")  # e.g., "mystore.myshopify.com"
            api_key = creds.get("api_key") or creds.get("access_token")
            api_version = creds.get("api_version", "2024-01")
            
            if not shop_domain or not api_key:
                return {"status": "error", "error": "Shopify Shop Domain and API Key required."}

            # 2. Connect to Real API
            base_url = f"https://{shop_domain}/admin/api/{api_version}"
            headers = {
                "X-Shopify-Access-Token": api_key,
                "Content-Type": "application/json"
            }
            
            action = self.get_config("action", "list_products")

            async with aiohttp.ClientSession() as session:
                if action == "list_products":
                    url = f"{base_url}/products.json"
                    async with session.get(url, headers=headers) as resp:
                        if resp.status != 200:
                            error_text = await resp.text()
                            return {"status": "error", "error": f"Shopify API Error {resp.status}: {error_text}"}
                        res_data = await resp.json()
                        return {"status": "success", "data": {"result": res_data.get("products", [])}}

                elif action == "create_product":
                    title = self.get_config("title")
                    price = self.get_config("price", "0.00")
                    
                    if not title:
                        return {"status": "error", "error": "title required"}
                    
                    url = f"{base_url}/products.json"
                    payload = {
                        "product": {
                            "title": title,
                            "variants": [{"price": price}]
                        }
                    }
                    async with session.post(url, headers=headers, json=payload) as resp:
                        if resp.status not in [200, 201]:
                            error_text = await resp.text()
                            return {"status": "error", "error": f"Shopify API Error {resp.status}: {error_text}"}
                        res_data = await resp.json()
                        return {"status": "success", "data": {"result": res_data.get("product", {})}}

                elif action == "update_inventory":
                    product_id = self.get_config("product_id")
                    inventory_quantity = self.get_config("inventory_quantity")
                    
                    if not product_id or not inventory_quantity:
                        return {"status": "error", "error": "product_id and inventory_quantity required"}
                    
                    # First get inventory item ID
                    url = f"{base_url}/products/{product_id}.json"
                    async with session.get(url, headers=headers) as resp:
                        if resp.status != 200:
                            return {"status": "error", "error": f"Product not found: {resp.status}"}
                        product_data = await resp.json()
                        
                    variant = product_data.get("product", {}).get("variants", [{}])[0]
                    inventory_item_id = variant.get("inventory_item_id")
                    
                    if not inventory_item_id:
                        return {"status": "error", "error": "No inventory item found"}
                    
                    # Get inventory levels
                    url = f"{base_url}/inventory_levels.json?inventory_item_ids={inventory_item_id}"
                    async with session.get(url, headers=headers) as resp:
                        if resp.status != 200:
                            return {"status": "error", "error": f"Inventory levels error: {resp.status}"}
                        inventory_data = await resp.json()
                    
                    location_id = inventory_data.get("inventory_levels", [{}])[0].get("location_id")
                    
                    # Update inventory
                    url = f"{base_url}/inventory_levels/set.json"
                    payload = {
                        "location_id": location_id,
                        "inventory_item_id": inventory_item_id,
                        "available": int(inventory_quantity)
                    }
                    async with session.post(url, headers=headers, json=payload) as resp:
                        if resp.status not in [200, 201]:
                            error_text = await resp.text()
                            return {"status": "error", "error": f"Inventory update error: {error_text}"}
                        res_data = await resp.json()
                        return {"status": "success", "data": {"result": res_data}}

                elif action == "list_orders":
                    url = f"{base_url}/orders.json"
                    async with session.get(url, headers=headers) as resp:
                        if resp.status != 200:
                            error_text = await resp.text()
                            return {"status": "error", "error": f"Shopify API Error {resp.status}: {error_text}"}
                        res_data = await resp.json()
                        return {"status": "success", "data": {"result": res_data.get("orders", [])}}

                elif action == "get_customer":
                    email = self.get_config("customer_email") or str(input_data)
                    url = f"{base_url}/customers/search.json?query=email:{email}"
                    async with session.get(url, headers=headers) as resp:
                        if resp.status != 200:
                            error_text = await resp.text()
                            return {"status": "error", "error": f"Shopify API Error {resp.status}: {error_text}"}
                        res_data = await resp.json()
                        return {"status": "success", "data": {"result": res_data.get("customers", [])}}

                return {"status": "error", "error": f"Unsupported action: {action}"}

        except Exception as e:
            return {"status": "error", "error": f"Shopify Node Failed: {str(e)}"}