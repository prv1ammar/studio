"""
Salesforce Node - Studio Standard (Universal Method)
Batch 108: Marketing & CRM
"""
from typing import Any, Dict, Optional
import aiohttp
from ...base import BaseNode
from ...registry import register_node

@register_node("salesforce_node")
class SalesforceNode(BaseNode):
    """
    Salesforce CRM integration for managing objects.
    """
    node_type = "salesforce_node"
    version = "1.0.0"
    category = "marketing"
    credentials_required = ["salesforce_auth"]

    inputs = {
        "action": {
            "type": "dropdown",
            "default": "create_record",
            "options": ["create_record", "get_record", "update_record", "search"],
            "description": "Salesforce action"
        },
        "sobject": {
            "type": "string",
            "default": "Account",
            "description": "Object type (e.g. Account, Contact, Lead)"
        },
        "data_json": {
            "type": "string",
            "optional": True,
            "description": "JSON body for record creation/update"
        },
        "record_id": {
            "type": "string",
            "optional": True
        },
        "query": {
            "type": "string",
            "optional": True,
            "description": "SOQL Query"
        }
    }

    outputs = {
        "result": {"type": "any"},
        "status": {"type": "string"}
    }

    async def execute(self, input_data: Any, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        try:
            creds = await self.get_credential("salesforce_auth")
            access_token = creds.get("access_token")
            instance_url = creds.get("instance_url")
            
            if not access_token or not instance_url:
                return {"status": "error", "error": "Salesforce access token and instance URL required"}

            api_version = "v57.0"
            base_url = f"{instance_url}/services/data/{api_version}"
            headers = {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json"
            }
            
            action = self.get_config("action", "create_record")

            async with aiohttp.ClientSession() as session:
                if action == "create_record":
                    sobject = self.get_config("sobject", "Account")
                    data_str = self.get_config("data_json", "{}")
                    
                    import json
                    try:
                        data = json.loads(data_str)
                    except:
                        return {"status": "error", "error": "Invalid JSON in data_json"}
                    
                    url = f"{base_url}/sobjects/{sobject}"
                    async with session.post(url, headers=headers, json=data) as resp:
                        if resp.status != 201:
                            error_text = await resp.text()
                            return {"status": "error", "error": f"Salesforce API Error {resp.status}: {error_text}"}
                        res_data = await resp.json()
                        return {"status": "success", "data": {"result": res_data}}
                
                elif action == "get_record":
                    sobject = self.get_config("sobject", "Account")
                    record_id = self.get_config("record_id")
                    if not record_id:
                        return {"status": "error", "error": "record_id required"}
                        
                    url = f"{base_url}/sobjects/{sobject}/{record_id}"
                    async with session.get(url, headers=headers) as resp:
                        res_data = await resp.json()
                        return {"status": "success", "data": {"result": res_data}}
                
                elif action == "search":
                    query = self.get_config("query")
                    if not query:
                        return {"status": "error", "error": "query (SOQL) required"}
                        
                    params = {"q": query}
                    url = f"{base_url}/query"
                    async with session.get(url, headers=headers, params=params) as resp:
                         res_data = await resp.json()
                         return {"status": "success", "data": {"result": res_data}}

            return {"status": "error", "error": f"Unsupported action: {action}"}

        except Exception as e:
            return {"status": "error", "error": f"Salesforce Node Failed: {str(e)}"}
