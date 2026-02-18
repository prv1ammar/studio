"""
Mollie Node - Studio Standard (Universal Method)
Batch 102: E-commerce & Payments Expansion
"""
from typing import Any, Dict, Optional, List
import aiohttp
from ..base import BaseNode
from ..registry import register_node

@register_node("mollie_node")
class MollieNode(BaseNode):
    """
    European payment gateway integration via Mollie API.
    """
    node_type = "mollie_node"
    version = "1.0.0"
    category = "finance"
    credentials_required = ["mollie_auth"]


    properties = [
        {
            'displayName': 'Operation',
            'name': 'operation',
            'type': 'options',
            'default': 'create_payment',
            'options': [
                {'name': 'Create Payment', 'value': 'create_payment'},
                {'name': 'Get Payment', 'value': 'get_payment'},
                {'name': 'List Payments', 'value': 'list_payments'},
                {'name': 'Create Customer', 'value': 'create_customer'},
                {'name': 'Create Subscription', 'value': 'create_subscription'},
                {'name': 'List Methods', 'value': 'list_methods'},
            ],
            'description': 'Mollie action',
        },
        {
            'displayName': 'Amount',
            'name': 'amount',
            'type': 'string',
            'default': '',
            'description': 'Amount (e.g., '10.00')',
        },
        {
            'displayName': 'Currency',
            'name': 'currency',
            'type': 'string',
            'default': 'EUR',
        },
        {
            'displayName': 'Customer Email',
            'name': 'customer_email',
            'type': 'string',
            'default': '',
        },
        {
            'displayName': 'Customer Name',
            'name': 'customer_name',
            'type': 'string',
            'default': '',
        },
        {
            'displayName': 'Description',
            'name': 'description',
            'type': 'string',
            'default': '',
        },
        {
            'displayName': 'Method',
            'name': 'method',
            'type': 'options',
            'default': '',
            'options': [
                {'name': 'Ideal', 'value': 'ideal'},
                {'name': 'Creditcard', 'value': 'creditcard'},
                {'name': 'Bancontact', 'value': 'bancontact'},
                {'name': 'Sofort', 'value': 'sofort'},
                {'name': 'Paypal', 'value': 'paypal'},
                {'name': 'Banktransfer', 'value': 'banktransfer'},
                {'name': 'Directdebit', 'value': 'directdebit'},
            ],
        },
        {
            'displayName': 'Payment Id',
            'name': 'payment_id',
            'type': 'string',
            'default': '',
        },
        {
            'displayName': 'Redirect Url',
            'name': 'redirect_url',
            'type': 'string',
            'default': '',
            'description': 'URL to redirect after payment',
        },
        {
            'displayName': 'Webhook Url',
            'name': 'webhook_url',
            'type': 'string',
            'default': '',
            'description': 'Webhook URL for payment updates',
        },
    ]
    inputs = {
        "action": {
            "type": "dropdown",
            "default": "create_payment",
            "options": ["create_payment", "get_payment", "list_payments", "create_customer", "create_subscription", "list_methods"],
            "description": "Mollie action"
        },
        "amount": {
            "type": "string",
            "optional": True,
            "description": "Amount (e.g., '10.00')"
        },
        "currency": {
            "type": "string",
            "default": "EUR",
            "optional": True
        },
        "description": {
            "type": "string",
            "optional": True
        },
        "redirect_url": {
            "type": "string",
            "optional": True,
            "description": "URL to redirect after payment"
        },
        "webhook_url": {
            "type": "string",
            "optional": True,
            "description": "Webhook URL for payment updates"
        },
        "payment_id": {
            "type": "string",
            "optional": True
        },
        "customer_name": {
            "type": "string",
            "optional": True
        },
        "customer_email": {
            "type": "string",
            "optional": True
        },
        "method": {
            "type": "dropdown",
            "options": ["ideal", "creditcard", "bancontact", "sofort", "paypal", "banktransfer", "directdebit"],
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
            creds = await self.get_credential("mollie_auth")
            api_key = creds.get("api_key")
            
            if not api_key:
                return {"status": "error", "error": "Mollie API Key required."}

            # 2. Connect to Real API
            base_url = "https://api.mollie.com/v2"
            
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            }
            
            action = self.get_config("action", "create_payment")

            async with aiohttp.ClientSession() as session:
                if action == "create_payment":
                    amount = self.get_config("amount")
                    currency = self.get_config("currency", "EUR")
                    description = self.get_config("description", "Payment")
                    redirect_url = self.get_config("redirect_url", "https://example.com/return")
                    
                    if not amount:
                        return {"status": "error", "error": "amount required"}
                    
                    url = f"{base_url}/payments"
                    payload = {
                        "amount": {
                            "currency": currency,
                            "value": amount
                        },
                        "description": description,
                        "redirectUrl": redirect_url
                    }
                    
                    # Optional fields
                    if self.get_config("webhook_url"):
                        payload["webhookUrl"] = self.get_config("webhook_url")
                    if self.get_config("method"):
                        payload["method"] = self.get_config("method")
                    
                    async with session.post(url, headers=headers, json=payload) as resp:
                        if resp.status not in [200, 201]:
                            error_text = await resp.text()
                            return {"status": "error", "error": f"Mollie API Error {resp.status}: {error_text}"}
                        res_data = await resp.json()
                        return {"status": "success", "data": {"result": res_data}}

                elif action == "get_payment":
                    payment_id = self.get_config("payment_id") or str(input_data)
                    
                    if not payment_id:
                        return {"status": "error", "error": "payment_id required"}
                    
                    url = f"{base_url}/payments/{payment_id}"
                    async with session.get(url, headers=headers) as resp:
                        if resp.status != 200:
                            error_text = await resp.text()
                            return {"status": "error", "error": f"Mollie API Error {resp.status}: {error_text}"}
                        res_data = await resp.json()
                        return {"status": "success", "data": {"result": res_data}}

                elif action == "list_payments":
                    url = f"{base_url}/payments"
                    async with session.get(url, headers=headers) as resp:
                        if resp.status != 200:
                            error_text = await resp.text()
                            return {"status": "error", "error": f"Mollie API Error {resp.status}: {error_text}"}
                        res_data = await resp.json()
                        return {"status": "success", "data": {"result": res_data.get("_embedded", {}).get("payments", [])}}

                elif action == "create_customer":
                    name = self.get_config("customer_name")
                    email = self.get_config("customer_email")
                    
                    if not name or not email:
                        return {"status": "error", "error": "customer_name and customer_email required"}
                    
                    url = f"{base_url}/customers"
                    payload = {
                        "name": name,
                        "email": email
                    }
                    
                    async with session.post(url, headers=headers, json=payload) as resp:
                        if resp.status not in [200, 201]:
                            error_text = await resp.text()
                            return {"status": "error", "error": f"Mollie API Error {resp.status}: {error_text}"}
                        res_data = await resp.json()
                        return {"status": "success", "data": {"result": res_data}}

                elif action == "create_subscription":
                    customer_id = self.get_config("payment_id")  # Reusing field
                    amount = self.get_config("amount")
                    currency = self.get_config("currency", "EUR")
                    interval = "1 month"  # Default interval
                    description = self.get_config("description", "Subscription")
                    
                    if not customer_id or not amount:
                        return {"status": "error", "error": "customer_id (via payment_id field) and amount required"}
                    
                    url = f"{base_url}/customers/{customer_id}/subscriptions"
                    payload = {
                        "amount": {
                            "currency": currency,
                            "value": amount
                        },
                        "interval": interval,
                        "description": description
                    }
                    
                    async with session.post(url, headers=headers, json=payload) as resp:
                        if resp.status not in [200, 201]:
                            error_text = await resp.text()
                            return {"status": "error", "error": f"Mollie API Error {resp.status}: {error_text}"}
                        res_data = await resp.json()
                        return {"status": "success", "data": {"result": res_data}}

                elif action == "list_methods":
                    url = f"{base_url}/methods"
                    async with session.get(url, headers=headers) as resp:
                        if resp.status != 200:
                            error_text = await resp.text()
                            return {"status": "error", "error": f"Mollie API Error {resp.status}: {error_text}"}
                        res_data = await resp.json()
                        return {"status": "success", "data": {"result": res_data.get("_embedded", {}).get("methods", [])}}

                return {"status": "error", "error": f"Unsupported action: {action}"}

        except Exception as e:
            return {"status": "error", "error": f"Mollie Node Failed: {str(e)}"}