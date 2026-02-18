"""
Airtable Node - Studio Standard (Universal Method)
Batch 91: Productivity Suite (n8n Critical)
"""
from typing import Any, Dict, Optional, List
import aiohttp
from ..base import BaseNode
from ..registry import register_node

@register_node("airtable_node")
class AirtableNode(BaseNode):
    """
    Manage records in Airtable bases via Airtable API.
    """
    node_type = "airtable_node"
    version = "1.0.0"
    category = "database"
    credentials_required = ["airtable_auth"]


    properties = [
        {
            'displayName': 'Operation',
            'name': 'operation',
            'type': 'options',
            'default': 'list_records',
            'options': [
                {'name': 'List Records', 'value': 'list_records'},
                {'name': 'Get Record', 'value': 'get_record'},
                {'name': 'Create Record', 'value': 'create_record'},
                {'name': 'Update Record', 'value': 'update_record'},
                {'name': 'Delete Record', 'value': 'delete_record'},
            ],
            'description': 'Airtable action',
        },
        {
            'displayName': 'Base Id',
            'name': 'base_id',
            'type': 'string',
            'default': '',
            'required': True,
        },
        {
            'displayName': 'Fields',
            'name': 'fields',
            'type': 'string',
            'default': '',
            'description': 'JSON object of fields',
        },
        {
            'displayName': 'Record Id',
            'name': 'record_id',
            'type': 'string',
            'default': '',
        },
        {
            'displayName': 'Table Name',
            'name': 'table_name',
            'type': 'string',
            'default': '',
            'required': True,
        },
    ]
    inputs = {
        "action": {
            "type": "dropdown",
            "default": "list_records",
            "options": ["list_records", "get_record", "create_record", "update_record", "delete_record"],
            "description": "Airtable action"
        },
        "base_id": {
            "type": "string",
            "required": True
        },
        "table_name": {
            "type": "string",
            "required": True
        },
        "record_id": {
            "type": "string",
            "optional": True
        },
        "fields": {
            "type": "string",
            "optional": True,
            "description": "JSON object of fields"
        }
    }

    outputs = {
        "result": {"type": "any"},
        "status": {"type": "string"}
    }

    async def execute(self, input_data: Any, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        try:
            # 1. Authentication
            creds = await self.get_credential("airtable_auth")
            api_key = creds.get("api_key")
            
            if not api_key:
                return {"status": "error", "error": "Airtable API Key required."}

            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            }
            
            # 2. Connect to Real API
            base_id = self.get_config("base_id")
            table_name = self.get_config("table_name")
            base_url = f"https://api.airtable.com/v0/{base_id}/{table_name}"
            action = self.get_config("action", "list_records")

            async with aiohttp.ClientSession() as session:
                if action == "list_records":
                    async with session.get(base_url, headers=headers) as resp:
                        if resp.status != 200:
                            return {"status": "error", "error": f"Airtable Error: {resp.status}"}
                        res_data = await resp.json()
                        return {"status": "success", "data": {"result": res_data.get("records", [])}}

                elif action == "get_record":
                    record_id = self.get_config("record_id") or str(input_data)
                    url = f"{base_url}/{record_id}"
                    async with session.get(url, headers=headers) as resp:
                        if resp.status != 200:
                            return {"status": "error", "error": f"Airtable Error: {resp.status}"}
                        res_data = await resp.json()
                        return {"status": "success", "data": {"result": res_data}}

                elif action == "create_record":
                    fields_str = self.get_config("fields", "{}")
                    import json
                    fields = json.loads(fields_str) if isinstance(fields_str, str) else fields_str
                    
                    payload = {"fields": fields}
                    async with session.post(base_url, headers=headers, json=payload) as resp:
                        if resp.status not in [200, 201]:
                            return {"status": "error", "error": f"Airtable Error: {resp.status}"}
                        res_data = await resp.json()
                        return {"status": "success", "data": {"result": res_data}}

                elif action == "update_record":
                    record_id = self.get_config("record_id")
                    fields_str = self.get_config("fields", "{}")
                    import json
                    fields = json.loads(fields_str) if isinstance(fields_str, str) else fields_str
                    
                    if not record_id:
                        return {"status": "error", "error": "record_id required"}
                    
                    url = f"{base_url}/{record_id}"
                    payload = {"fields": fields}
                    async with session.patch(url, headers=headers, json=payload) as resp:
                        if resp.status != 200:
                            return {"status": "error", "error": f"Airtable Error: {resp.status}"}
                        res_data = await resp.json()
                        return {"status": "success", "data": {"result": res_data}}

                return {"status": "error", "error": f"Unsupported action: {action}"}

        except Exception as e:
            return {"status": "error", "error": f"Airtable Node Failed: {str(e)}"}