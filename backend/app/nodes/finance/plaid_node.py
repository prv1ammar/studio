"""
Plaid Node - Studio Standard (Universal Method)
Batch 102: E-commerce & Payments Expansion
"""
from typing import Any, Dict, Optional, List
import aiohttp
from ...base import BaseNode
from ...registry import register_node

@register_node("plaid_node")
class PlaidNode(BaseNode):
    """
    Banking and financial data access via Plaid API.
    """
    node_type = "plaid_node"
    version = "1.0.0"
    category = "finance"
    credentials_required = ["plaid_auth"]

    inputs = {
        "action": {
            "type": "dropdown",
            "default": "create_link_token",
            "options": ["create_link_token", "exchange_public_token", "get_accounts", "get_transactions", "get_balance", "get_identity"],
            "description": "Plaid action"
        },
        "public_token": {
            "type": "string",
            "optional": True,
            "description": "Public token from Plaid Link"
        },
        "access_token": {
            "type": "string",
            "optional": True,
            "description": "Access token for API calls"
        },
        "start_date": {
            "type": "string",
            "optional": True,
            "description": "Start date for transactions (YYYY-MM-DD)"
        },
        "end_date": {
            "type": "string",
            "optional": True,
            "description": "End date for transactions (YYYY-MM-DD)"
        },
        "user_id": {
            "type": "string",
            "optional": True,
            "description": "Unique user ID for link token"
        }
    }

    outputs = {
        "result": {"type": "any"},
        "status": {"type": "string"}
    }

    async def execute(self, input_data: Any, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        try:
            # 1. Authentication
            creds = await self.get_credential("plaid_auth")
            client_id = creds.get("client_id")
            secret = creds.get("secret")
            environment = creds.get("environment", "sandbox")  # sandbox, development, or production
            
            if not client_id or not secret:
                return {"status": "error", "error": "Plaid Client ID and Secret required."}

            # 2. Connect to Real API
            env_urls = {
                "sandbox": "https://sandbox.plaid.com",
                "development": "https://development.plaid.com",
                "production": "https://production.plaid.com"
            }
            base_url = env_urls.get(environment, "https://sandbox.plaid.com")
            
            headers = {
                "Content-Type": "application/json"
            }
            
            action = self.get_config("action", "create_link_token")

            async with aiohttp.ClientSession() as session:
                if action == "create_link_token":
                    user_id = self.get_config("user_id", "default_user")
                    
                    url = f"{base_url}/link/token/create"
                    payload = {
                        "client_id": client_id,
                        "secret": secret,
                        "user": {
                            "client_user_id": user_id
                        },
                        "client_name": "Studio Automation",
                        "products": ["auth", "transactions"],
                        "country_codes": ["US"],
                        "language": "en"
                    }
                    
                    async with session.post(url, headers=headers, json=payload) as resp:
                        if resp.status != 200:
                            error_text = await resp.text()
                            return {"status": "error", "error": f"Plaid API Error {resp.status}: {error_text}"}
                        res_data = await resp.json()
                        return {"status": "success", "data": {"result": res_data}}

                elif action == "exchange_public_token":
                    public_token = self.get_config("public_token") or str(input_data)
                    
                    if not public_token:
                        return {"status": "error", "error": "public_token required"}
                    
                    url = f"{base_url}/item/public_token/exchange"
                    payload = {
                        "client_id": client_id,
                        "secret": secret,
                        "public_token": public_token
                    }
                    
                    async with session.post(url, headers=headers, json=payload) as resp:
                        if resp.status != 200:
                            error_text = await resp.text()
                            return {"status": "error", "error": f"Plaid API Error {resp.status}: {error_text}"}
                        res_data = await resp.json()
                        return {"status": "success", "data": {"result": res_data}}

                elif action == "get_accounts":
                    access_token = self.get_config("access_token") or str(input_data)
                    
                    if not access_token:
                        return {"status": "error", "error": "access_token required"}
                    
                    url = f"{base_url}/accounts/get"
                    payload = {
                        "client_id": client_id,
                        "secret": secret,
                        "access_token": access_token
                    }
                    
                    async with session.post(url, headers=headers, json=payload) as resp:
                        if resp.status != 200:
                            error_text = await resp.text()
                            return {"status": "error", "error": f"Plaid API Error {resp.status}: {error_text}"}
                        res_data = await resp.json()
                        return {"status": "success", "data": {"result": res_data.get("accounts", [])}}

                elif action == "get_transactions":
                    access_token = self.get_config("access_token")
                    start_date = self.get_config("start_date", "2024-01-01")
                    end_date = self.get_config("end_date", "2024-12-31")
                    
                    if not access_token:
                        return {"status": "error", "error": "access_token required"}
                    
                    url = f"{base_url}/transactions/get"
                    payload = {
                        "client_id": client_id,
                        "secret": secret,
                        "access_token": access_token,
                        "start_date": start_date,
                        "end_date": end_date
                    }
                    
                    async with session.post(url, headers=headers, json=payload) as resp:
                        if resp.status != 200:
                            error_text = await resp.text()
                            return {"status": "error", "error": f"Plaid API Error {resp.status}: {error_text}"}
                        res_data = await resp.json()
                        return {"status": "success", "data": {"result": res_data.get("transactions", [])}}

                elif action == "get_balance":
                    access_token = self.get_config("access_token") or str(input_data)
                    
                    if not access_token:
                        return {"status": "error", "error": "access_token required"}
                    
                    url = f"{base_url}/accounts/balance/get"
                    payload = {
                        "client_id": client_id,
                        "secret": secret,
                        "access_token": access_token
                    }
                    
                    async with session.post(url, headers=headers, json=payload) as resp:
                        if resp.status != 200:
                            error_text = await resp.text()
                            return {"status": "error", "error": f"Plaid API Error {resp.status}: {error_text}"}
                        res_data = await resp.json()
                        return {"status": "success", "data": {"result": res_data.get("accounts", [])}}

                elif action == "get_identity":
                    access_token = self.get_config("access_token") or str(input_data)
                    
                    if not access_token:
                        return {"status": "error", "error": "access_token required"}
                    
                    url = f"{base_url}/identity/get"
                    payload = {
                        "client_id": client_id,
                        "secret": secret,
                        "access_token": access_token
                    }
                    
                    async with session.post(url, headers=headers, json=payload) as resp:
                        if resp.status != 200:
                            error_text = await resp.text()
                            return {"status": "error", "error": f"Plaid API Error {resp.status}: {error_text}"}
                        res_data = await resp.json()
                        return {"status": "success", "data": {"result": res_data}}

                return {"status": "error", "error": f"Unsupported action: {action}"}

        except Exception as e:
            return {"status": "error", "error": f"Plaid Node Failed: {str(e)}"}
