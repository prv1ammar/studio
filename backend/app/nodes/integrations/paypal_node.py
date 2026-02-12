import aiohttp
import json
import base64
from typing import Any, Dict, Optional
from ..base import BaseNode
from ..registry import register_node

@register_node("paypal_action")
class PayPalNode(BaseNode):
    """Integrates with PayPal for orders and payouts."""
    node_type = "paypal_action"
    version = "1.0.0"
    category = "integrations"
    credentials_required = ["paypal_auth"]

    inputs = {
        "action": {"type": "string", "enum": ["create_order", "list_payouts"], "default": "create_order"},
        "mode": {"type": "string", "enum": ["sandbox", "live"], "default": "sandbox"},
        "data": {"type": "any", "description": "Order amount or full data dict"}
    }
    outputs = {
        "result": {"type": "object"},
        "status": {"type": "string"}
    }

    async def _get_access_token(self, session: aiohttp.ClientSession, client_id: str, client_secret: str, base_url: str):
        auth_string = f"{client_id}:{client_secret}"
        auth_encoded = base64.b64encode(auth_string.encode()).decode()
        
        headers = {
            "Authorization": f"Basic {auth_encoded}",
            "Content-Type": "application/x-www-form-urlencoded"
        }
        
        async with session.post(f"{base_url}/v1/oauth2/token", data="grant_type=client_credentials", headers=headers) as resp:
            data = await resp.json()
            return data.get("access_token")

    async def execute(self, input_data: Any, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        # 1. Auth Retrieval
        creds = await self.get_credential("paypal_auth")
        client_id = creds.get("client_id") if creds else self.get_config("client_id")
        client_secret = creds.get("client_secret") if creds else self.get_config("client_secret")
        mode = self.get_config("mode", "sandbox")

        if not client_id or not client_secret:
            return {"status": "error", "error": "PayPal Client ID and Secret are required.", "data": None}

        base_url = "https://api-m.sandbox.paypal.com" if mode == "sandbox" else "https://api-m.paypal.com"
        action = self.get_config("action", "create_order")

        async with aiohttp.ClientSession() as session:
            try:
                token = await self._get_access_token(session, client_id, client_secret, base_url)
                if not token:
                    return {"status": "error", "error": "Failed to get PayPal access token.", "data": None}

                headers = {
                    "Authorization": f"Bearer {token}",
                    "Content-Type": "application/json"
                }

                if action == "create_order":
                    url = f"{base_url}/v2/checkout/orders"
                    if isinstance(input_data, (int, float, str)) and not isinstance(input_data, dict):
                         payload = {
                            "intent": "CAPTURE",
                            "purchase_units": [{
                                "amount": {
                                    "currency_code": "USD",
                                    "value": str(input_data)
                                }
                            }]
                        }
                    else:
                        payload = input_data
                    
                    async with session.post(url, json=payload, headers=headers) as resp:
                        result = await resp.json()
                        return {
                            "status": "success" if resp.status < 400 else "error",
                            "data": result,
                            "error": result.get("message") if resp.status >= 400 else None
                        }

                elif action == "list_payouts":
                    url = f"{base_url}/v1/payments/payouts"
                    async with session.get(url, headers=headers) as resp:
                        result = await resp.json()
                        return {
                            "status": "success" if resp.status < 400 else "error",
                            "data": result,
                            "error": result.get("message") if resp.status >= 400 else None
                        }

                return {"status": "error", "error": f"Unsupported PayPal action: {action}", "data": None}

            except Exception as e:
                return {"status": "error", "error": f"PayPal Node Failed: {str(e)}", "data": None}
