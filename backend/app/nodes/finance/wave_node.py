"""
Wave Node - Studio Standard (Universal Method)
Batch 85: SMB Finance
"""
from typing import Any, Dict, Optional, List
import aiohttp
from ..base import BaseNode
from ..registry import register_node

@register_node("wave_node")
class WaveNode(BaseNode):
    """
    Orchestrate bookkeeping and invoices for small businesses via Wave GraphQL API.
    """
    node_type = "wave_node"
    version = "1.0.0"
    category = "finance"
    credentials_required = ["wave_auth"]


    properties = [
        {
            'displayName': 'Operation',
            'name': 'operation',
            'type': 'options',
            'default': 'list_businesses',
            'options': [
                {'name': 'List Businesses', 'value': 'list_businesses'},
                {'name': 'List Invoices', 'value': 'list_invoices'},
                {'name': 'Get Account Details', 'value': 'get_account_details'},
                {'name': 'Create Invoice', 'value': 'create_invoice'},
            ],
            'description': 'Wave GraphQL action',
        },
        {
            'displayName': 'Business Id',
            'name': 'business_id',
            'type': 'string',
            'default': '',
            'description': 'The unique ID of the business in Wave.',
        },
    ]
    inputs = {
        "action": {
            "type": "dropdown",
            "default": "list_businesses",
            "options": ["list_businesses", "list_invoices", "get_account_details", "create_invoice"],
            "description": "Wave GraphQL action"
        },
        "business_id": {
            "type": "string",
            "optional": True,
            "description": "The unique ID of the business in Wave."
        }
    }

    outputs = {
        "result": {"type": "any"},
        "status": {"type": "string"},
        "error": {"type": "string", "optional": True}
    }

    async def execute(self, input_data: Any, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        try:
            # 1. Authentication First
            creds = await self.get_credential("wave_auth")
            access_token = creds.get("access_token") if creds else self.get_config("access_token")
            
            if not access_token:
                return {"status": "error", "error": "Wave Access Token (OAuth2) is required."}

            headers = {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json",
                "Accept": "application/json"
            }
            
            # 2. Connect to Real API (GraphQL)
            url = "https://gql.waveapps.com/graphql/public"
            action = self.get_config("action", "list_businesses")
            biz_id = self.get_config("business_id") or (str(input_data) if isinstance(input_data, str) else None)

            async with aiohttp.ClientSession() as session:
                # 3. Clear Actions & 4. Standard i/o
                if action == "list_businesses":
                    query = "{ businesses(page: 1, pageSize: 10) { edges { node { id name isPersonal } } } }"
                    payload = {"query": query}
                    async with session.post(url, headers=headers, json=payload) as resp:
                        # 5. Error Handling
                        if resp.status != 200:
                            return {"status": "error", "error": f"Wave API Error: {resp.status} - {await resp.text()}"}
                        res_data = await resp.json()
                        return {"status": "success", "data": {"result": res_data.get("data", {}).get("businesses", {}).get("edges", [])}}

                elif action == "list_invoices":
                    if not biz_id:
                        return {"status": "error", "error": "business_id is required for list_invoices action."}
                    query = f'{{ business(id: "{biz_id}") {{ invoices(page: 1, pageSize: 10) {{ edges {{ node {{ id invoiceNumber status total {{ value currency {{ code }} }} }} }} }} }} }}'
                    payload = {"query": query}
                    async with session.post(url, headers=headers, json=payload) as resp:
                        if resp.status != 200:
                            return {"status": "error", "error": f"Wave API Error: {resp.status}"}
                        res_data = await resp.json()
                        return {"status": "success", "data": {"result": res_data.get("data", {}).get("business", {}).get("invoices", {}).get("edges", [])}}

                return {"status": "error", "error": f"Unsupported action: {action}"}

        except Exception as e:
            # 5. Error Handling
            return {"status": "error", "error": f"Wave Node Failed: {str(e)}"}