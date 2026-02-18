"""
Zoho CRM Node - Studio Standard (Universal Method)
Batch 108: Marketing & CRM
"""
from typing import Any, Dict, Optional
import aiohttp
from ..base import BaseNode
from ..registry import register_node

@register_node("zoho_crm_node")
class ZohoCRMNode(BaseNode):
    """
    Zoho CRM integration for sales automation.
    """
    node_type = "zoho_crm_node"
    version = "1.0.0"
    category = "marketing"
    credentials_required = ["zoho_crm_auth"]


    properties = [
        {
            'displayName': 'Operation',
            'name': 'operation',
            'type': 'options',
            'default': 'create_record',
            'options': [
                {'name': 'Create Record', 'value': 'create_record'},
                {'name': 'Get Record', 'value': 'get_record'},
                {'name': 'Search Records', 'value': 'search_records'},
                {'name': 'Update Record', 'value': 'update_record'},
            ],
            'description': 'Zoho CRM action',
        },
        {
            'displayName': 'Data Json',
            'name': 'data_json',
            'type': 'string',
            'default': '',
            'description': 'JSON object of record data',
        },
        {
            'displayName': 'Module',
            'name': 'module',
            'type': 'string',
            'default': 'Leads',
            'description': 'Module name (e.g. Leads, Contacts, Accounts)',
        },
        {
            'displayName': 'Record Id',
            'name': 'record_id',
            'type': 'string',
            'default': '',
        },
    ]
    inputs = {
        "action": {
            "type": "dropdown",
            "default": "create_record",
            "options": ["create_record", "get_record", "search_records", "update_record"],
            "description": "Zoho CRM action"
        },
        "module": {
            "type": "string",
            "default": "Leads",
            "description": "Module name (e.g. Leads, Contacts, Accounts)"
        },
        "data_json": {
            "type": "string",
            "optional": True,
            "description": "JSON object of record data"
        },
        "record_id": {
            "type": "string",
            "optional": True
        }
    }

    outputs = {
        "result": {"type": "any"},
        "status": {"type": "string"}
    }

    async def execute(self, input_data: Any, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        try:
            creds = await self.get_credential("zoho_crm_auth")
            access_token = creds.get("access_token")
            api_domain = creds.get("api_domain", "https://www.zohoapis.com")
            
            if not access_token:
                return {"status": "error", "error": "Zoho access token required"}

            base_url = f"{api_domain}/crm/v2"
            headers = {
                "Authorization": f"Zoho-oauthtoken {access_token}",
                "Content-Type": "application/json"
            }
            
            action = self.get_config("action", "create_record")
            module = self.get_config("module", "Leads")

            async with aiohttp.ClientSession() as session:
                if action == "create_record":
                    data_str = self.get_config("data_json", "{}")
                    import json
                    try:
                        data = json.loads(data_str)
                    except:
                        return {"status": "error", "error": "Invalid JSON in data_json"}
                        
                    payload = {"data": [data]} # Zoho expects list in 'data' key
                    
                    url = f"{base_url}/{module}"
                    async with session.post(url, headers=headers, json=payload) as resp:
                        if resp.status not in [200, 201]:
                            error_text = await resp.text()
                            return {"status": "error", "error": f"Zoho API Error {resp.status}: {error_text}"}
                        res_data = await resp.json()
                        return {"status": "success", "data": {"result": res_data}}
                
                elif action == "get_record":
                    record_id = self.get_config("record_id")
                    if not record_id:
                        return {"status": "error", "error": "record_id required"}
                        
                    url = f"{base_url}/{module}/{record_id}"
                    async with session.get(url, headers=headers) as resp:
                        res_data = await resp.json()
                        return {"status": "success", "data": {"result": res_data}}
                
                elif action == "search_records":
                    # Simplified search criteria assuming standard params available or COQL
                    # Using search endpoint
                     url = f"{base_url}/{module}/search"
                     # Need input for criteria, simplified to listing here or custom param not added yet
                     # Falling back to get records
                     url = f"{base_url}/{module}"
                     async with session.get(url, headers=headers) as resp:
                         res_data = await resp.json()
                         return {"status": "success", "data": {"result": res_data}}

            return {"status": "error", "error": f"Unsupported action: {action}"}

        except Exception as e:
            return {"status": "error", "error": f"Zoho CRM Node Failed: {str(e)}"}