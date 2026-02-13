"""
Sage Node - Studio Standard
Batch 84: Enterprise Finance
"""
from typing import Any, Dict, Optional, List
import aiohttp
from ...base import BaseNode
from ...registry import register_node

@register_node("sage_node")
class SageNode(BaseNode):
    """
    Manage core accounting and payroll workflows via Sage Business Cloud API.
    """
    node_type = "sage_node"
    version = "1.0.0"
    category = "finance"
    credentials_required = ["sage_auth"]

    inputs = {
        "action": {
            "type": "dropdown",
            "default": "get_sales_invoices",
            "options": ["get_sales_invoices", "get_contacts", "list_ledger_accounts"],
            "description": "Sage action"
        }
    }

    outputs = {
        "result": {"type": "any"},
        "status": {"type": "string"}
    }

    async def execute(self, input_data: Any, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        try:
            creds = await self.get_credential("sage_auth")
            access_token = creds.get("access_token")
            
            if not access_token:
                return {"status": "error", "error": "Sage Access Token is required."}

            headers = {
                "Authorization": f"Bearer {access_token}",
                "Accept": "application/json",
                "Content-Type": "application/json"
            }
            
            base_url = "https://api.columbus.sage.com/sagebusinesscloud/v3.1"
            action = self.get_config("action", "get_sales_invoices")

            async with aiohttp.ClientSession() as session:
                if action == "get_sales_invoices":
                    url = f"{base_url}/sales_invoices"
                    async with session.get(url, headers=headers) as resp:
                        res_data = await resp.json()
                        return {"status": "success", "data": {"result": res_data}}
                
                elif action == "get_contacts":
                    url = f"{base_url}/contacts"
                    async with session.get(url, headers=headers) as resp:
                        res_data = await resp.json()
                        return {"status": "success", "data": {"result": res_data}}

                return {"status": "error", "error": f"Unsupported action: {action}"}
        except Exception as e:
            return {"status": "error", "error": f"Sage Node Failed: {str(e)}"}
