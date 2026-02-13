"""
QuickBooks Node - Studio Standard
Batch 58: Financial Services
"""
from typing import Any, Dict, Optional, List
import aiohttp
from ...base import BaseNode
from ...registry import register_node

@register_node("quickbooks_node")
class QuickBooksNode(BaseNode):
    """
    Automate QuickBooks accounting tasks including Invoices, Customers, and Expenses.
    """
    node_type = "quickbooks_node"
    version = "1.1.0"
    category = "finance"
    credentials_required = ["quickbooks_auth"]

    inputs = {
        "action": {
            "type": "dropdown",
            "default": "list_customers",
            "options": ["list_customers", "list_invoices", "create_customer", "get_company_info", "list_accounts"],
            "description": "QuickBooks action to perform"
        },
        "query": {
            "type": "string",
            "optional": True,
            "description": "Custom SQL-like query (e.g., 'SELECT * FROM Item WHERE Active = true')"
        },
        "is_sandbox": {
            "type": "boolean",
            "default": True,
            "description": "Use QuickBooks Sandbox environment"
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
                "Accept": "application/json",
                "Content-Type": "application/json"
            }

            async with aiohttp.ClientSession() as session:
                if action == "get_company_info":
                    url = f"{base_url}/v3/company/{realm_id}/companyinfo/{realm_id}"
                    async with session.get(url, headers=headers) as resp:
                        res_data = await resp.json()
                        return {"status": "success", "data": {"result": res_data.get("CompanyInfo"), "status": "fetched"}}

                # SQL-like query actions
                query_map = {
                    "list_customers": "SELECT * FROM Customer",
                    "list_invoices": "SELECT * FROM Invoice",
                    "list_accounts": "SELECT * FROM Account"
                }
                
                query = self.get_config("query") or query_map.get(action)
                if not query:
                     return {"status": "error", "error": f"No query defined for action: {action}"}

                url = f"{base_url}/v3/company/{realm_id}/query?query={query}"
                async with session.get(url, headers=headers) as resp:
                    result = await resp.json()
                    if resp.status >= 400:
                         return {"status": "error", "error": f"QuickBooks API Error: {result}"}
                    
                    # Extract entity list from QueryResponse
                    query_res = result.get("QueryResponse", {})
                    # Find the first list in the response (Intuit nests it under the Entity name)
                    entity_list = []
                    for k, v in query_res.items():
                        if isinstance(v, list):
                            entity_list = v
                            break
                    
                    return {
                        "status": "success",
                        "data": {
                            "result": entity_list,
                            "count": len(entity_list),
                            "status": "completed"
                        }
                    }

        except Exception as e:
            return {"status": "error", "error": f"QuickBooks Node Failed: {str(e)}"}
