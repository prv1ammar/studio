"""
Square Node - Studio Standard (Universal Method)
Batch 102: E-commerce & Payments Expansion
"""
from typing import Any, Dict, Optional, List
import aiohttp
from ...base import BaseNode
from ...registry import register_node

@register_node("square_node")
class SquareNode(BaseNode):
    """
    Square POS and payment processing integration.
    """
    node_type = "square_node"
    version = "1.0.0"
    category = "finance"
    credentials_required = ["square_auth"]

    inputs = {
        "action": {
            "type": "dropdown",
            "default": "create_payment",
            "options": ["create_payment", "list_customers", "create_customer", "list_locations", "create_invoice", "get_payment"],
            "description": "Square action"
        },
        "amount": {
            "type": "string",
            "optional": True,
            "description": "Amount in cents (e.g., 1000 for $10.00)"
        },
        "currency": {
            "type": "string",
            "default": "USD",
            "optional": True
        },
        "source_id": {
            "type": "string",
            "optional": True,
            "description": "Payment source (card nonce)"
        },
        "customer_id": {
            "type": "string",
            "optional": True
        },
        "email": {
            "type": "string",
            "optional": True
        },
        "given_name": {
            "type": "string",
            "optional": True
        },
        "family_name": {
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
            creds = await self.get_credential("square_auth")
            access_token = creds.get("access_token")
            environment = creds.get("environment", "production")  # production or sandbox
            
            if not access_token:
                return {"status": "error", "error": "Square Access Token required."}

            # 2. Connect to Real API
            if environment == "sandbox":
                base_url = "https://connect.squareupsandbox.com/v2"
            else:
                base_url = "https://connect.squareup.com/v2"
            
            headers = {
                "Square-Version": "2024-01-18",
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json"
            }
            
            action = self.get_config("action", "create_payment")

            async with aiohttp.ClientSession() as session:
                if action == "create_payment":
                    amount = self.get_config("amount")
                    currency = self.get_config("currency", "USD")
                    source_id = self.get_config("source_id")
                    
                    if not amount or not source_id:
                        return {"status": "error", "error": "amount and source_id required"}
                    
                    import uuid
                    url = f"{base_url}/payments"
                    payload = {
                        "source_id": source_id,
                        "idempotency_key": str(uuid.uuid4()),
                        "amount_money": {
                            "amount": int(amount),
                            "currency": currency
                        }
                    }
                    
                    async with session.post(url, headers=headers, json=payload) as resp:
                        if resp.status not in [200, 201]:
                            error_text = await resp.text()
                            return {"status": "error", "error": f"Square API Error {resp.status}: {error_text}"}
                        res_data = await resp.json()
                        return {"status": "success", "data": {"result": res_data.get("payment", {})}}

                elif action == "list_customers":
                    url = f"{base_url}/customers"
                    async with session.get(url, headers=headers) as resp:
                        if resp.status != 200:
                            error_text = await resp.text()
                            return {"status": "error", "error": f"Square API Error {resp.status}: {error_text}"}
                        res_data = await resp.json()
                        return {"status": "success", "data": {"result": res_data.get("customers", [])}}

                elif action == "create_customer":
                    email = self.get_config("email")
                    given_name = self.get_config("given_name")
                    family_name = self.get_config("family_name")
                    
                    if not email:
                        return {"status": "error", "error": "email required"}
                    
                    import uuid
                    url = f"{base_url}/customers"
                    payload = {
                        "idempotency_key": str(uuid.uuid4()),
                        "email_address": email
                    }
                    
                    if given_name:
                        payload["given_name"] = given_name
                    if family_name:
                        payload["family_name"] = family_name
                    
                    async with session.post(url, headers=headers, json=payload) as resp:
                        if resp.status not in [200, 201]:
                            error_text = await resp.text()
                            return {"status": "error", "error": f"Square API Error {resp.status}: {error_text}"}
                        res_data = await resp.json()
                        return {"status": "success", "data": {"result": res_data.get("customer", {})}}

                elif action == "list_locations":
                    url = f"{base_url}/locations"
                    async with session.get(url, headers=headers) as resp:
                        if resp.status != 200:
                            error_text = await resp.text()
                            return {"status": "error", "error": f"Square API Error {resp.status}: {error_text}"}
                        res_data = await resp.json()
                        return {"status": "success", "data": {"result": res_data.get("locations", [])}}

                elif action == "get_payment":
                    payment_id = str(input_data) if input_data else self.get_config("source_id")
                    if not payment_id:
                        return {"status": "error", "error": "payment_id required"}
                    
                    url = f"{base_url}/payments/{payment_id}"
                    async with session.get(url, headers=headers) as resp:
                        if resp.status != 200:
                            error_text = await resp.text()
                            return {"status": "error", "error": f"Square API Error {resp.status}: {error_text}"}
                        res_data = await resp.json()
                        return {"status": "success", "data": {"result": res_data.get("payment", {})}}

                return {"status": "error", "error": f"Unsupported action: {action}"}

        except Exception as e:
            return {"status": "error", "error": f"Square Node Failed: {str(e)}"}
