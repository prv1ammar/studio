"""
FreshBooks Node - Studio Standard (Universal Method)
Batch 85: SMB Finance
"""
from typing import Any, Dict, Optional, List
import aiohttp
from ...base import BaseNode
from ...registry import register_node

@register_node("freshbooks_node")
class FreshBooksNode(BaseNode):
    """
    Orchestrate client invoicing and time tracking via FreshBooks REST API.
    """
    node_type = "freshbooks_node"
    version = "1.0.0"
    category = "finance"
    credentials_required = ["freshbooks_auth"]

    inputs = {
        "action": {
            "type": "dropdown",
            "default": "get_identity",
            "options": ["get_identity", "list_invoices", "list_clients", "get_account_details"],
            "description": "FreshBooks action"
        },
        "account_id": {
            "type": "string",
            "optional": True,
            "description": "FreshBooks Account ID (required for invoices/clients)."
        }
    }

    outputs = {
        "result": {"type": "any"},
        "status": {"type": "string"},
        "account_id": {"type": "string", "optional": True}
    }

    async def execute(self, input_data: Any, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        try:
            # 1. Authentication First
            creds = await self.get_credential("freshbooks_auth")
            access_token = creds.get("access_token") if creds else self.get_config("access_token")
            
            if not access_token:
                return {"status": "error", "error": "FreshBooks Access Token (OAuth2) is required."}

            headers = {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json",
                "Accept": "application/json"
            }
            
            # 2. Connect to Real API
            base_url = "https://api.freshbooks.com"
            action = self.get_config("action", "get_identity")
            acc_id = self.get_config("account_id")

            async with aiohttp.ClientSession() as session:
                # Action: Get Identity (to find account_id if not provided)
                if action == "get_identity":
                    url = f"{base_url}/auth/api/v1/users/me"
                    async with session.get(url, headers=headers) as resp:
                        if resp.status != 200:
                            return {"status": "error", "error": f"FreshBooks Auth Error: {resp.status}"}
                        res_data = await resp.json()
                        # Extract first account_id for convenience
                        memberships = res_data.get("response", {}).get("memberships", [])
                        found_acc_id = memberships[0].get("account_id") if memberships else None
                        return {"status": "success", "data": {"result": res_data.get("response"), "account_id": str(found_acc_id)}}

                # Action: List Invoices
                elif action == "list_invoices":
                    if not acc_id:
                        return {"status": "error", "error": "account_id is required to list invoices."}
                    url = f"{base_url}/accounting/carter/accounts/{acc_id}/invoices/invoices"
                    async with session.get(url, headers=headers) as resp:
                        if resp.status != 200:
                            return {"status": "error", "error": f"FreshBooks API Error: {resp.status}"}
                        res_data = await resp.json()
                        return {"status": "success", "data": {"result": res_data.get("response", {}).get("result", {}).get("invoices", [])}}

                return {"status": "error", "error": f"Unsupported action: {action}"}

        except Exception as e:
            # 5. Error Handling
            return {"status": "error", "error": f"FreshBooks Node Failed: {str(e)}"}
