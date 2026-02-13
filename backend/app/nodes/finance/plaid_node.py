"""
Plaid Node - Studio Standard
Batch 58: Financial Services
"""
from typing import Any, Dict, Optional, List
import aiohttp
from ...base import BaseNode
from ...registry import register_node

@register_node("plaid_node")
class PlaidNode(BaseNode):
    """
    Connect to bank accounts and retrieve financial data via Plaid.
    """
    node_type = "plaid_node"
    version = "1.0.0"
    category = "finance"
    credentials_required = ["plaid_auth"]

    inputs = {
        "action": {
            "type": "dropdown",
            "default": "get_accounts",
            "options": ["get_accounts", "get_transactions", "get_auth", "get_identity", "get_balance"],
            "description": "Plaid action to perform"
        },
        "access_token": {
            "type": "string",
            "required": True,
            "description": "The access token for the specific item/bank account"
        },
        "environment": {
            "type": "dropdown",
            "default": "sandbox",
            "options": ["sandbox", "development", "production"],
            "description": "Plaid environment to use"
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
        }
    }

    outputs = {
        "result": {"type": "any"},
        "status": {"type": "string"},
        "count": {"type": "number"}
    }

    async def execute(self, input_data: Any, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        try:
            # 1. Resolve Auth
            creds = await self.get_credential("plaid_auth")
            client_id = creds.get("client_id") if creds else self.get_config("client_id")
            secret = creds.get("secret") if creds else self.get_config("secret")
            access_token = self.get_config("access_token") or (str(input_data) if isinstance(input_data, str) and input_data.startswith("access-") else None)
            
            if not all([client_id, secret, access_token]):
                return {"status": "error", "error": "Plaid Client ID, Secret, and Access Token are required."}

            env = self.get_config("environment", "sandbox")
            base_url = f"https://{env}.plaid.com"
            action = self.get_config("action", "get_accounts")

            headers = {
                "Content-Type": "application/json",
                "Plaid-Client-Id": client_id,
                "Plaid-Secret": secret
            }
            
            async with aiohttp.ClientSession() as session:
                payload = {"access_token": access_token}

                if action == "get_accounts":
                    url = f"{base_url}/accounts/get"
                elif action == "get_transactions":
                    url = f"{base_url}/transactions/get"
                    payload["start_date"] = self.get_config("start_date", "2024-01-01")
                    payload["end_date"] = self.get_config("end_date", "2024-12-31")
                elif action == "get_auth":
                    url = f"{base_url}/auth/get"
                elif action == "get_identity":
                    url = f"{base_url}/identity/get"
                elif action == "get_balance":
                    url = f"{base_url}/accounts/balance/get"
                else:
                    return {"status": "error", "error": f"Unsupported Plaid action: {action}"}

                async with session.post(url, headers=headers, json=payload) as resp:
                    res_data = await resp.json()
                    if resp.status >= 400:
                        return {"status": "error", "error": f"Plaid API Error: {res_data}"}
                    
                    return {
                        "status": "success",
                        "data": {
                            "result": res_data,
                            "status": "completed",
                            "count": len(res_data.get("accounts", [])) if "accounts" in res_data else len(res_data.get("transactions", [])) if "transactions" in res_data else 1
                        }
                    }

        except Exception as e:
            return {"status": "error", "error": f"Plaid Node Failed: {str(e)}"}
