import aiohttp
from typing import Any, Dict, Optional, List
from ..base import BaseNode
from ..registry import register_node

@register_node("quickbooks_node")
class QuickbooksNode(BaseNode):
    """
    Automate QuickBooks actions (Customers, Invoices, etc.).
    """
    node_type = "quickbooks_node"
    version = "1.0.0"
    category = "integrations"
    credentials_required = ["quickbooks_auth"]

    inputs = {
        "action": {"type": "string", "default": "list_customers", "enum": ["list_customers", "list_invoices"]},
        "is_sandbox": {"type": "boolean", "default": True}
    }
    outputs = {
        "results": {"type": "array"},
        "status": {"type": "string"}
    }

    async def execute(self, input_data: Any, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        try:
            # 1. Resolve Auth
            creds = await self.get_credential("quickbooks_auth")
            token = creds.get("token") or creds.get("access_token") if creds else self.get_config("access_token")
            realm_id = creds.get("realm_id") if creds else self.get_config("realm_id")
            is_sandbox = self.get_config("is_sandbox", True)

            if not token or not realm_id:
                return {"status": "error", "error": "QuickBooks Access Token and Realm ID are required."}

            base_url = "https://sandbox-quickbooks.api.intuit.com" if is_sandbox else "https://quickbooks.api.intuit.com"
            action = self.get_config("action", "list_customers")
            
            headers = {
                "Authorization": f"Bearer {token}",
                "Accept": "application/json"
            }

            async with aiohttp.ClientSession() as session:
                if action == "list_customers":
                    query = "SELECT * FROM Customer"
                elif action == "list_invoices":
                    query = "SELECT * FROM Invoice"
                else:
                    return {"status": "error", "error": f"Unsupported action: {action}"}

                url = f"{base_url}/v3/company/{realm_id}/query?query={query}"
                async with session.get(url, headers=headers) as resp:
                    result = await resp.json()
                    data = result.get("QueryResponse", {}).get(action.split("_")[1].capitalize(), [])
                    
                    return {
                        "status": "success",
                        "data": {
                            "results": data,
                            "count": len(data)
                        }
                    }

        except Exception as e:
            return {"status": "error", "error": f"QuickBooks Node Error: {str(e)}"}
