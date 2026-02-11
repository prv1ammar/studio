import aiohttp
import json
import base64
from typing import Any, Dict, Optional
from pydantic import Field
from app.nodes.base import BaseNode, NodeConfig
from app.nodes.registry import register_node

class PayPalConfig(NodeConfig):
    client_id: Optional[str] = Field(None, description="PayPal Client ID")
    client_secret: Optional[str] = Field(None, description="PayPal Secret")
    mode: str = Field("sandbox", description="sandbox or live")
    credentials_id: Optional[str] = Field(None, description="PayPal Credentials ID")
    action: str = Field("create_order", description="Action (create_order, list_payouts)")

@register_node("paypal_node")
class PayPalNode(BaseNode):
    node_id = "paypal_node"
    config_model = PayPalConfig

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

    async def execute(self, input_data: Any, context: Optional[Dict[str, Any]] = None) -> Any:
        # 1. Auth Retrieval
        creds = await self.get_credential("credentials_id")
        client_id = creds.get("client_id") if creds else self.get_config("client_id")
        client_secret = creds.get("client_secret") if creds else self.get_config("client_secret")
        mode = self.get_config("mode")

        if not client_id or not client_secret:
            return {"error": "PayPal Client ID and Secret are required."}

        base_url = "https://api-m.sandbox.paypal.com" if mode == "sandbox" else "https://api-m.paypal.com"
        action = self.get_config("action")

        async with aiohttp.ClientSession() as session:
            try:
                token = await self._get_access_token(session, client_id, client_secret, base_url)
                if not token:
                    return {"error": "Failed to get PayPal access token."}

                headers = {
                    "Authorization": f"Bearer {token}",
                    "Content-Type": "application/json"
                }

                if action == "create_order":
                    url = f"{base_url}/v2/checkout/orders"
                    # Default payload if simple amount given
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
                        return result

                elif action == "list_payouts":
                    url = f"{base_url}/v1/payments/payouts"
                    async with session.get(url, headers=headers) as resp:
                        result = await resp.json()
                        return result

                return {"error": f"Unsupported PayPal action: {action}"}

            except Exception as e:
                return {"error": f"PayPal Node Failed: {str(e)}"}
