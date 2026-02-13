"""
NetSuite Node - Studio Standard
Batch 84: Enterprise Finance
"""
from typing import Any, Dict, Optional, List
import aiohttp
from ...base import BaseNode
from ...registry import register_node

@register_node("netsuite_node")
class NetSuiteNode(BaseNode):
    """
    Search items, invoices, and accounting records via NetSuite SuiteTalk API.
    """
    node_type = "netsuite_node"
    version = "1.0.0"
    category = "finance"
    credentials_required = ["netsuite_auth"]

    inputs = {
        "action": {
            "type": "dropdown",
            "default": "list_invoices",
            "options": ["list_invoices", "get_customer", "search_items", "create_sales_order"],
            "description": "NetSuite action"
        },
        "account_id": {
            "type": "string",
            "required": True,
            "description": "NetSuite Account ID (e.g. 1234567-sb1)"
        }
    }

    outputs = {
        "result": {"type": "any"},
        "status": {"type": "string"}
    }

    async def execute(self, input_data: Any, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        try:
            creds = await self.get_credential("netsuite_auth")
            # NetSuite REST uses OAuth 2.0 or TBA
            access_token = creds.get("access_token") if creds else self.get_config("access_token")
            
            if not access_token:
                return {"status": "error", "error": "NetSuite Access Token is required."}

            account_id = self.get_config("account_id").replace("_", "-").lower()
            headers = {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json",
                "Accept": "application/json"
            }
            
            base_url = f"https://{account_id}.suitetalk.api.netsuite.com/services/rest/record/v1"
            action = self.get_config("action", "list_invoices")

            async with aiohttp.ClientSession() as session:
                if action == "list_invoices":
                    url = f"{base_url}/invoice"
                    async with session.get(url, headers=headers) as resp:
                        res_data = await resp.json()
                        return {"status": "success", "data": {"result": res_data.get("items", [])}}

                elif action == "get_customer":
                    cust_id = str(input_data)
                    url = f"{base_url}/customer/{cust_id}"
                    async with session.get(url, headers=headers) as resp:
                        res_data = await resp.json()
                        return {"status": "success", "data": {"result": res_data}}

                return {"status": "error", "error": f"Unsupported action: {action}"}
        except Exception as e:
            return {"status": "error", "error": f"NetSuite Node Failed: {str(e)}"}
