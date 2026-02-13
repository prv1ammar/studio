"""
LemonSqueezy Node - Studio Standard
Batch 52: Commerce Expansion
"""
from typing import Any, Dict, Optional, List
import aiohttp
from ...base import BaseNode
from ...registry import register_node

@register_node("lemonsqueezy_node")
class LemonSqueezyNode(BaseNode):
    """
    Manage LemonSqueezy store data, subscriptions, and orders.
    """
    node_type = "lemonsqueezy_node"
    version = "1.0.0"
    category = "commerce"
    credentials_required = ["lemonsqueezy_auth"]

    inputs = {
        "action": {
            "type": "dropdown",
            "default": "list_orders",
            "options": ["list_orders", "get_order", "list_subscriptions", "get_subscription", "get_user"],
            "description": "LemonSqueezy action to perform"
        },
        "item_id": {
            "type": "string",
            "optional": True,
            "description": "Specific Order or Subscription ID"
        }
    }

    outputs = {
        "result": {"type": "any"},
        "status": {"type": "string"}
    }

    async def execute(self, input_data: Any, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        try:
            # 1. Resolve Auth
            creds = await self.get_credential("lemonsqueezy_auth")
            api_key = creds.get("api_key") if creds else self.get_config("api_key")
            
            if not api_key:
                return {"status": "error", "error": "LemonSqueezy API Key is required."}

            action = self.get_config("action", "list_orders")
            item_id = self.get_config("item_id") or (str(input_data) if isinstance(input_data, (str, int)) else None)

            headers = {
                "Authorization": f"Bearer {api_key}",
                "Accept": "application/vnd.api+json",
                "Content-Type": "application/vnd.api+json"
            }
            
            base_api_url = "https://api.lemonsqueezy.com/v1"

            async with aiohttp.ClientSession() as session:
                if action == "get_user":
                    url = f"{base_api_url}/users/me"
                    async with session.get(url, headers=headers) as resp:
                        result = await resp.json()
                        return {
                            "status": "success",
                            "data": {"result": result.get("data"), "status": "fetched"}
                        }

                elif action == "list_orders":
                    url = f"{base_api_url}/orders"
                    async with session.get(url, headers=headers) as resp:
                        result = await resp.json()
                        return {
                            "status": "success",
                            "data": {"result": result.get("data"), "count": len(result.get("data", []))}
                        }

                elif action == "get_order":
                    if not item_id:
                         return {"status": "error", "error": "Order ID is required."}
                    url = f"{base_api_url}/orders/{item_id}"
                    async with session.get(url, headers=headers) as resp:
                        result = await resp.json()
                        return {
                            "status": "success",
                            "data": {"result": result.get("data"), "status": "fetched"}
                        }

                elif action == "list_subscriptions":
                    url = f"{base_api_url}/subscriptions"
                    async with session.get(url, headers=headers) as resp:
                        result = await resp.json()
                        return {
                            "status": "success",
                            "data": {"result": result.get("data"), "count": len(result.get("data", []))}
                        }

                elif action == "get_subscription":
                    if not item_id:
                         return {"status": "error", "error": "Subscription ID is required."}
                    url = f"{base_api_url}/subscriptions/{item_id}"
                    async with session.get(url, headers=headers) as resp:
                        result = await resp.json()
                        return {
                            "status": "success",
                            "data": {"result": result.get("data"), "status": "fetched"}
                        }

                return {"status": "error", "error": f"Unsupported LemonSqueezy action: {action}"}

        except Exception as e:
            return {"status": "error", "error": f"LemonSqueezy execution failed: {str(e)}"}
