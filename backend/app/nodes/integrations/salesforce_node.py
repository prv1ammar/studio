from typing import Any, Dict, Optional, List
from ..base import BaseNode
from ..registry import register_node

@register_node("salesforce_crm")
class SalesforceNode(BaseNode):
    """
    Automate Salesforce CRM actions (Leads, Contacts, etc.).
    """
    node_type = "salesforce_crm"
    version = "1.0.0"
    category = "integrations"
    credentials_required = ["salesforce_auth"]

    inputs = {
        "object_type": {"type": "string", "default": "Lead"},
        "record_data": {"type": "object", "optional": True}
    }
    outputs = {
        "id": {"type": "string"},
        "success": {"type": "boolean"},
        "status": {"type": "string"}
    }

    async def execute(self, input_data: Any, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        try:
            from simple_salesforce import Salesforce
        except ImportError:
            return {"status": "error", "error": "Please install 'simple-salesforce'."}

        try:
            # 1. Resolve Auth
            creds = await self.get_credential("salesforce_auth")
            username = creds.get("username") if creds else self.get_config("username")
            password = creds.get("password") if creds else self.get_config("password")
            token = creds.get("security_token") if creds else self.get_config("security_token")
            domain = self.get_config("domain", "login")

            if not all([username, password, token]):
                return {"status": "error", "error": "Salesforce Username, Password, and Security Token are required."}

            sf = Salesforce(username=username, password=password, security_token=token, domain=domain)
            
            # 2. Perform Action (Default to Create)
            obj_type = self.get_config("object_type", "Lead")
            data = input_data if isinstance(input_data, dict) else self.get_config("record_data", {})
            
            if not data:
                return {"status": "error", "error": "Record data dictionary is required."}

            res = sf.__getattr__(obj_type).create(data)
            
            return {
                "status": "success",
                "data": {
                    "id": res.get("id"),
                    "success": res.get("success", True),
                    "object": obj_type
                }
            }

        except Exception as e:
            return {"status": "error", "error": f"Salesforce Node Error: {str(e)}"}
