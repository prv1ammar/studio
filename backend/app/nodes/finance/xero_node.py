"""
Xero Node - Studio Standard
Batch 84: Enterprise Finance
"""
from typing import Any, Dict, Optional, List
import aiohttp
from ..base import BaseNode
from ..registry import register_node

@register_node("xero_node")
class XeroNode(BaseNode):
    """
    Orchestrate invoices, bank syncs, and reports via Xero API.
    """
    node_type = "xero_node"
    version = "1.0.0"
    category = "finance"
    credentials_required = ["xero_auth"]


    properties = [
        {
            'displayName': 'Operation',
            'name': 'operation',
            'type': 'options',
            'default': 'get_invoices',
            'options': [
                {'name': 'Get Invoices', 'value': 'get_invoices'},
                {'name': 'Get Accounts', 'value': 'get_accounts'},
                {'name': 'List Contacts', 'value': 'list_contacts'},
                {'name': 'Create Invoice', 'value': 'create_invoice'},
            ],
            'description': 'Xero action',
        },
        {
            'displayName': 'Tenant Id',
            'name': 'tenant_id',
            'type': 'string',
            'default': '',
            'description': 'Xero Tenant ID',
            'required': True,
        },
    ]
    inputs = {
        "action": {
            "type": "dropdown",
            "default": "get_invoices",
            "options": ["get_invoices", "get_accounts", "list_contacts", "create_invoice"],
            "description": "Xero action"
        },
        "tenant_id": {
            "type": "string",
            "required": True,
            "description": "Xero Tenant ID"
        }
    }

    outputs = {
        "result": {"type": "any"},
        "status": {"type": "string"}
    }

    async def execute(self, input_data: Any, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        try:
            creds = await self.get_credential("xero_auth")
            access_token = creds.get("access_token") if creds else self.get_config("access_token")
            tenant_id = self.get_config("tenant_id")
            
            if not access_token or not tenant_id:
                return {"status": "error", "error": "Xero Access Token and Tenant ID are required."}

            headers = {
                "Authorization": f"Bearer {access_token}",
                "Xero-tenant-id": tenant_id,
                "Accept": "application/json"
            }
            
            base_url = "https://api.xero.com/api.xro/2.0"
            action = self.get_config("action", "get_invoices")

            async with aiohttp.ClientSession() as session:
                if action == "get_invoices":
                    url = f"{base_url}/Invoices"
                    async with session.get(url, headers=headers) as resp:
                        res_data = await resp.json()
                        return {"status": "success", "data": {"result": res_data.get("Invoices", [])}}

                elif action == "list_contacts":
                    url = f"{base_url}/Contacts"
                    async with session.get(url, headers=headers) as resp:
                        res_data = await resp.json()
                        return {"status": "success", "data": {"result": res_data.get("Contacts", [])}}

                return {"status": "error", "error": f"Unsupported action: {action}"}
        except Exception as e:
            return {"status": "error", "error": f"Xero Node Failed: {str(e)}"}