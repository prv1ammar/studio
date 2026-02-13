"""
Shopify Commerce Node - Studio Standard
Batch 52: Commerce Expansion
"""
from typing import Any, Dict, Optional, List
import aiohttp
from ...base import BaseNode
from ...registry import register_node

@register_node("shopify_node")
class ShopifyNode(BaseNode):
    """
    Manage Shopify store data including Products, Orders, and Customers.
    """
    node_type = "shopify_node"
    version = "1.0.0"
    category = "commerce"
    credentials_required = ["shopify_auth"]

    inputs = {
        "action": {
            "type": "dropdown",
            "default": "list_products",
            "options": ["list_products", "get_product", "list_orders", "get_order", "list_customers"],
            "description": "Shopify action to perform"
        },
        "shop_url": {
            "type": "string",
            "required": True,
            "description": "Store URL (e.g., 'your-store.myshopify.com')"
        },
        "item_id": {
            "type": "string",
            "optional": True,
            "description": "Specific Product or Order ID"
        },
        "limit": {
            "type": "number",
            "default": 10,
            "description": "Number of results to return"
        }
    }

    outputs = {
        "result": {"type": "any"},
        "count": {"type": "number"},
        "status": {"type": "string"}
    }

    async def execute(self, input_data: Any, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        try:
            # 1. Resolve Auth
            creds = await self.get_credential("shopify_auth")
            access_token = None
            shop_url = self.get_config("shop_url")
            
            if creds:
                access_token = creds.get("access_token") or creds.get("api_password")
                shop_url = creds.get("shop_url") or shop_url
            
            if not access_token:
                access_token = self.get_config("access_token")

            if not access_token or not shop_url:
                return {"status": "error", "error": "Shopify Access Token and Shop URL are required."}

            # Normalize Shop URL
            shop_url = shop_url.replace("https://", "").replace("http://", "").rstrip("/")
            if not shop_url.endswith("myshopify.com") and "." not in shop_url:
                shop_url = f"{shop_url}.myshopify.com"

            action = self.get_config("action", "list_products")
            limit = int(self.get_config("limit", 10))
            item_id = self.get_config("item_id") or (str(input_data) if isinstance(input_data, (str, int)) and not str(input_data).startswith("http") else None)

            headers = {
                "X-Shopify-Access-Token": access_token,
                "Content-Type": "application/json"
            }
            
            base_api_url = f"https://{shop_url}/admin/api/2024-01"

            async with aiohttp.ClientSession() as session:
                if action == "list_products":
                    url = f"{base_api_url}/products.json"
                    params = {"limit": limit}
                    async with session.get(url, headers=headers, params=params) as resp:
                        result = await resp.json()
                        products = result.get("products", [])
                        return {
                            "status": "success",
                            "data": {"result": products, "count": len(products)}
                        }

                elif action == "get_product":
                    if not item_id:
                         return {"status": "error", "error": "Product ID is required."}
                    url = f"{base_api_url}/products/{item_id}.json"
                    async with session.get(url, headers=headers) as resp:
                        result = await resp.json()
                        return {
                            "status": "success",
                            "data": {"result": result.get("product"), "status": "fetched"}
                        }

                elif action == "list_orders":
                    url = f"{base_api_url}/orders.json"
                    params = {"limit": limit, "status": "any"}
                    async with session.get(url, headers=headers, params=params) as resp:
                        result = await resp.json()
                        orders = result.get("orders", [])
                        return {
                            "status": "success",
                            "data": {"result": orders, "count": len(orders)}
                        }

                elif action == "get_order":
                    if not item_id:
                         return {"status": "error", "error": "Order ID is required."}
                    url = f"{base_api_url}/orders/{item_id}.json"
                    async with session.get(url, headers=headers) as resp:
                        result = await resp.json()
                        return {
                            "status": "success",
                            "data": {"result": result.get("order"), "status": "fetched"}
                        }

                elif action == "list_customers":
                    url = f"{base_api_url}/customers.json"
                    params = {"limit": limit}
                    async with session.get(url, headers=headers, params=params) as resp:
                        result = await resp.json()
                        customers = result.get("customers", [])
                        return {
                            "status": "success",
                            "data": {"result": customers, "count": len(customers)}
                        }

                return {"status": "error", "error": f"Unsupported Shopify action: {action}"}

        except Exception as e:
            return {"status": "error", "error": f"Shopify execution failed: {str(e)}"}
