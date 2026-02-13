"""
SAP Node - Studio Standard
Batch 84: Enterprise Finance
"""
from typing import Any, Dict, Optional, List
import aiohttp
from ...base import BaseNode
from ...registry import register_node

@register_node("sap_node")
class SAPNode(BaseNode):
    """
    Orchestrate ERP workflows and financial data via SAP OData or NetWeaver Gateway APIs.
    """
    node_type = "sap_node"
    version = "1.0.0"
    category = "finance"
    credentials_required = ["sap_auth"]

    inputs = {
        "action": {
            "type": "dropdown",
            "default": "get_purchase_orders",
            "options": ["get_purchase_orders", "get_sales_orders", "get_supplier_info", "create_purchase_order"],
            "description": "SAP OData action"
        },
        "base_url": {
            "type": "string",
            "required": True,
            "description": "SAP S/4HANA or Business One OData URL"
        }
    }

    outputs = {
        "result": {"type": "any"},
        "status": {"type": "string"}
    }

    async def execute(self, input_data: Any, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        try:
            creds = await self.get_credential("sap_auth")
            # SAP often uses Basic Auth or OAuth2
            access_token = creds.get("access_token") if creds else self.get_config("access_token")
            user = creds.get("username")
            password = creds.get("password")
            
            headers = {"Accept": "application/json", "Content-Type": "application/json"}
            if access_token:
                headers["Authorization"] = f"Bearer {access_token}"
            elif user and password:
                import base64
                auth = base64.b64encode(f"{user}:{password}".encode()).decode()
                headers["Authorization"] = f"Basic {auth}"
            else:
                return {"status": "error", "error": "SAP Credentials (OAuth or Basic) required."}

            base_url = self.get_config("base_url").rstrip("/")
            action = self.get_config("action", "get_purchase_orders")

            async with aiohttp.ClientSession() as session:
                if action == "get_purchase_orders":
                    url = f"{base_url}/API_PURCHASEORDER_PROCESS_SRV/A_PurchaseOrder"
                    async with session.get(url, headers=headers) as resp:
                        res_data = await resp.json()
                        return {"status": "success", "data": {"result": res_data.get("d", {}).get("results", [])}}

                elif action == "get_sales_orders":
                    url = f"{base_url}/API_SALES_ORDER_SRV/A_SalesOrder"
                    async with session.get(url, headers=headers) as resp:
                        res_data = await resp.json()
                        return {"status": "success", "data": {"result": res_data.get("d", {}).get("results", [])}}

                return {"status": "error", "error": f"Unsupported action: {action}"}
        except Exception as e:
            return {"status": "error", "error": f"SAP Node Failed: {str(e)}"}
