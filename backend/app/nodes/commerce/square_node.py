"""
Square Node - Studio Standard (Universal Method)
Batch 90: CRM & Marketing (n8n Critical)
"""
from typing import Any, Dict, Optional, List
import aiohttp
import uuid
from ...base import BaseNode
from ...registry import register_node

@register_node("square_node")
class SquareNode(BaseNode):
    """
    Process payments and manage orders via Square API.
    """
    node_type = "square_node"
    version = "1.0.0"
    category = "commerce"
    credentials_required = ["square_auth"]

    inputs = {
        "action": {
            "type": "dropdown",
            "default": "list_payments",
            "options": ["list_payments", "create_payment", "list_orders", "get_location"],
            "description": "Square action"
        },
        "amount": {
            "type": "number",
            "optional": True
        },
        "currency": {
            "type": "string",
            "default": "USD",
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
            creds = await self.get_credential("square_auth")
            access_token = creds.get("access_token")
            
            if not access_token:
                return {"status": "error", "error": "Square Access Token required."}

            headers = {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json",
                "Square-Version": "2024-01-18"
            }
            
            # 2. Connect to Real API
            base_url = "https://connect.squareup.com/v2"
            action = self.get_config("action", "list_payments")

            async with aiohttp.ClientSession() as session:
                if action == "list_payments":
                    url = f"{base_url}/payments"
                    async with session.get(url, headers=headers) as resp:
                        if resp.status != 200:
                            return {"status": "error", "error": f"Square Error: {resp.status}"}
                        res_data = await resp.json()
                        return {"status": "success", "data": {"result": res_data.get("payments", [])}}

                elif action == "create_payment":
                    amount = int(self.get_config("amount", 100))
                    currency = self.get_config("currency", "USD")
                    
                    url = f"{base_url}/payments"
                    payload = {
                        "source_id": "CASH",  # Simplified for demo
                        "idempotency_key": str(uuid.uuid4()),
                        "amount_money": {
                            "amount": amount,
                            "currency": currency
                        }
                    }
                    async with session.post(url, headers=headers, json=payload) as resp:
                        if resp.status not in [200, 201]:
                            return {"status": "error", "error": f"Square Error: {resp.status}"}
                        res_data = await resp.json()
                        return {"status": "success", "data": {"result": res_data.get("payment", {})}}

                elif action == "list_orders":
                    url = f"{base_url}/orders/search"
                    payload = {
                        "limit": 10
                    }
                    async with session.post(url, headers=headers, json=payload) as resp:
                        if resp.status != 200:
                            return {"status": "error", "error": f"Square Error: {resp.status}"}
                        res_data = await resp.json()
                        return {"status": "success", "data": {"result": res_data.get("orders", [])}}

                elif action == "get_location":
                    url = f"{base_url}/locations"
                    async with session.get(url, headers=headers) as resp:
                        if resp.status != 200:
                            return {"status": "error", "error": f"Square Error: {resp.status}"}
                        res_data = await resp.json()
                        return {"status": "success", "data": {"result": res_data.get("locations", [])}}

                return {"status": "error", "error": f"Unsupported action: {action}"}

        except Exception as e:
            return {"status": "error", "error": f"Square Node Failed: {str(e)}"}
