"""
Salesforce Integration Node - Studio Standard
Batch 44: SaaS Integrations
"""
from typing import Any, Dict, Optional, List
from ...base import BaseNode
from ...registry import register_node

@register_node("salesforce_node")
class SalesforceNode(BaseNode):
    """
    Automate Salesforce CRM actions.
    Supports: Create Record, Query SOQL, Get Record.
    """
    node_type = "salesforce_node"
    version = "1.0.0"
    category = "saas"
    credentials_required = ["salesforce_auth"]

    inputs = {
        "action": {
            "type": "dropdown",
            "default": "create_record",
            "options": ["create_record", "query_soql", "get_record"],
            "description": "Salesforce action to perform"
        },
        "object_type": {
            "type": "dropdown",
            "default": "Lead",
            "options": ["Lead", "Contact", "Account", "Opportunity", "Case", "Task"],
            "description": "Standard Salesforce object type"
        },
        "payload": {
            "type": "json",
            "description": "JSON object with record fields"
        },
        "query": {
            "type": "string",
            "description": "SOQL Query (for query_soql action)"
        },
        "record_id": {
            "type": "string",
            "optional": True,
            "description": "Specific Record ID"
        }
    }

    outputs = {
        "id": {"type": "string"},
        "result": {"type": "object"},
        "records": {"type": "array"}
    }

    async def execute(self, input_data: Any, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        try:
            from simple_salesforce import Salesforce
        except ImportError:
            return {"status": "error", "error": "simple-salesforce not installed. Run: pip install simple-salesforce"}

        try:
            # 1. Resolve Auth
            creds = await self.get_credential("salesforce_auth")
            username = None
            password = None
            token = None
            domain = self.get_config("domain", "login")

            if creds:
                username = creds.get("username")
                password = creds.get("password")
                token = creds.get("security_token") or creds.get("token")
            
            if not all([username, password, token]):
                username = self.get_config("username")
                password = self.get_config("password")
                token = self.get_config("security_token")

            if not all([username, password, token]):
                return {"status": "error", "error": "Credentials missing: Username, Password, and Security Token are required."}

            # Build Client
            sf = Salesforce(username=username, password=password, security_token=token, domain=domain)
            
            action = self.get_config("action", "create_record")
            obj_type = self.get_config("object_type", "Lead")
            
            result_data = {}

            if action == "create_record":
                data = self.get_config("payload", {})
                if isinstance(input_data, dict):
                    data.update(input_data)
                
                if not data:
                     return {"status": "error", "error": "Record data is required for creation."}
                
                response = sf.__getattr__(obj_type).create(data)
                result_data = {
                    "id": response.get("id"),
                    "success": response.get("success", True),
                    "object": obj_type
                }

            elif action == "query_soql":
                soql = self.get_config("query")
                if isinstance(input_data, str) and input_data.upper().startswith("SELECT"):
                    soql = input_data
                
                if not soql:
                     return {"status": "error", "error": "SOQL query is required."}

                response = sf.query(soql)
                result_data = {
                    "records": response.get("records", []),
                    "total": response.get("totalSize", 0),
                    "done": response.get("done", True)
                }

            elif action == "get_record":
                record_id = self.get_config("record_id") or (input_data if isinstance(input_data, str) else None)
                if not record_id:
                     return {"status": "error", "error": "Record ID is required."}
                
                response = sf.__getattr__(obj_type).get(record_id)
                result_data = {
                    "id": record_id,
                    "item": response,
                    "object": obj_type
                }

            else:
                 return {"status": "error", "error": f"Unknown action: {action}"}

            return {
                "status": "success",
                "data": result_data
            }

        except Exception as e:
            return {"status": "error", "error": f"Salesforce execution failed: {str(e)}"}
