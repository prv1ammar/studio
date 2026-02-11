import aiohttp
from typing import Any, Dict, Optional
from pydantic import Field
from app.nodes.base import BaseNode, NodeConfig
from app.nodes.registry import register_node

class QuickbooksConfig(NodeConfig):
    access_token: Optional[str] = Field(None, description="Quickbooks OAuth2 Access Token")
    realm_id: Optional[str] = Field(None, description="Quickbooks Company/Realm ID")
    is_sandbox: bool = Field(True, description="Use QuickBooks Sandbox")
    credentials_id: Optional[str] = Field(None, description="Quickbooks Credentials ID")
    action: str = Field("list_customers", description="Action (list_customers, list_invoices)")

@register_node("quickbooks_node")
class QuickbooksNode(BaseNode):
    node_id = "quickbooks_node"
    config_model = QuickbooksConfig

    async def execute(self, input_data: Any, context: Optional[Dict[str, Any]] = None) -> Any:
        # 1. Auth Retrieval
        creds = await self.get_credential("credentials_id")
        token = creds.get("token") if creds else self.get_config("access_token")
        realm_id = creds.get("realm_id") if creds else self.get_config("realm_id")
        is_sandbox = self.get_config("is_sandbox")

        if not token or not realm_id:
            return {"error": "Quickbooks Access Token and Realm ID are required."}

        base_url = "https://sandbox-quickbooks.api.intuit.com" if is_sandbox else "https://quickbooks.api.intuit.com"
        action = self.get_config("action")
        
        headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/json"
        }

        async with aiohttp.ClientSession() as session:
            try:
                if action == "list_customers":
                    query = "SELECT * FROM Customer"
                    url = f"{base_url}/v3/company/{realm_id}/query?query={query}"
                    async with session.get(url, headers=headers) as resp:
                        result = await resp.json()
                        return result.get("QueryResponse", {}).get("Customer", [])

                elif action == "list_invoices":
                    query = "SELECT * FROM Invoice"
                    url = f"{base_url}/v3/company/{realm_id}/query?query={query}"
                    async with session.get(url, headers=headers) as resp:
                        result = await resp.json()
                        return result.get("QueryResponse", {}).get("Invoice", [])

                return {"error": f"Unsupported Quickbooks action: {action}"}

            except Exception as e:
                return {"error": f"Quickbooks Node Failed: {str(e)}"}
