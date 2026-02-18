"""
Brex Node - Studio Standard (Universal Method)
Batch 85: SMB Finance
"""
from typing import Any, Dict, Optional, List
import aiohttp
from ..base import BaseNode
from ..registry import register_node

@register_node("brex_node")
class BrexNode(BaseNode):
    """
    High-growth business banking and expense orchestration via Brex REST API.
    """
    node_type = "brex_node"
    version = "1.0.0"
    category = "finance"
    credentials_required = ["brex_auth"]


    properties = [
        {
            'displayName': 'Operation',
            'name': 'operation',
            'type': 'options',
            'default': 'list_accounts',
            'options': [
                {'name': 'List Accounts', 'value': 'list_accounts'},
                {'name': 'List Transfers', 'value': 'list_transfers'},
                {'name': 'List Cards', 'value': 'list_cards'},
                {'name': 'Get Company', 'value': 'get_company'},
            ],
            'description': 'Brex action',
        },
    ]
    inputs = {
        "action": {
            "type": "dropdown",
            "default": "list_accounts",
            "options": ["list_accounts", "list_transfers", "list_cards", "get_company"],
            "description": "Brex action"
        }
    }

    outputs = {
        "result": {"type": "any"},
        "status": {"type": "string"},
        "count": {"type": "number", "optional": True}
    }

    async def execute(self, input_data: Any, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        try:
            # 1. Authentication First
            creds = await self.get_credential("brex_auth")
            access_token = creds.get("access_token") if creds else self.get_config("access_token")
            
            if not access_token:
                return {"status": "error", "error": "Brex Access Token (OAuth2) is required."}

            headers = {
                "Authorization": f"Bearer {access_token}",
                "Accept": "application/json",
                "Content-Type": "application/json"
            }
            
            # 2. Connect to Real API
            # Brex uses different subdomains for different APIs
            action = self.get_config("action", "list_accounts")

            async with aiohttp.ClientSession() as session:
                if action == "list_accounts":
                    url = "https://platform.brexapis.com/v2/accounts"
                    async with session.get(url, headers=headers) as resp:
                        if resp.status != 200:
                            return {"status": "error", "error": f"Brex API Error: {resp.status} - {await resp.text()}"}
                        res_data = await resp.json()
                        return {"status": "success", "data": {"result": res_data}}

                elif action == "list_transfers":
                    url = "https://platform.brexapis.com/v2/transfers"
                    async with session.get(url, headers=headers) as resp:
                        if resp.status != 200:
                            return {"status": "error", "error": f"Brex API Error: {resp.status}"}
                        res_data = await resp.json()
                        items = res_data.get("items", [])
                        return {"status": "success", "data": {"result": items, "count": len(items)}}

                elif action == "get_company":
                    url = "https://platform.brexapis.com/v2/company"
                    async with session.get(url, headers=headers) as resp:
                        if resp.status != 200:
                            return {"status": "error", "error": f"Brex API Error: {resp.status}"}
                        res_data = await resp.json()
                        return {"status": "success", "data": {"result": res_data}}

                return {"status": "error", "error": f"Unsupported action: {action}"}

        except Exception as e:
            # 5. Error Handling
            return {"status": "error", "error": f"Brex Node Failed: {str(e)}"}