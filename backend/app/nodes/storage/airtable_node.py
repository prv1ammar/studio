import json
from typing import Any, Dict, Optional, List
from ..base import BaseNode
from ..registry import register_node
import aiohttp

@register_node("airtable_action")
class AirtableNode(BaseNode):
    """
    Automate Airtable actions (Read/Write records).
    """
    node_type = "airtable_action"
    version = "1.0.0"
    category = "storage"
    credentials_required = ["airtable_auth"]


    properties = [
        {
            'displayName': 'Operation',
            'name': 'operation',
            'type': 'string',
            'default': 'read_records',
        },
        {
            'displayName': 'Base Id',
            'name': 'base_id',
            'type': 'string',
            'default': '',
            'description': 'Airtable Base ID',
        },
        {
            'displayName': 'Data',
            'name': 'data',
            'type': 'string',
            'default': '',
            'description': 'Fields for writing',
        },
        {
            'displayName': 'Table Name',
            'name': 'table_name',
            'type': 'string',
            'default': '',
            'description': 'Table Name or ID',
        },
    ]
    inputs = {
        "action": {"type": "string", "default": "read_records", "enum": ["read_records", "write_record"]},
        "base_id": {"type": "string", "description": "Airtable Base ID"},
        "table_name": {"type": "string", "description": "Table Name or ID"},
        "data": {"type": "object", "optional": True, "description": "Fields for writing"}
    }
    outputs = {
        "records": {"type": "array"},
        "id": {"type": "string"},
        "status": {"type": "string"}
    }

    async def execute(self, input_data: Any, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        try:
            # 1. Resolve Auth
            creds = await self.get_credential("airtable_auth")
            token = creds.get("token") or creds.get("api_key") if creds else self.get_config("api_key")
            
            base_id = self.get_config("base_id")
            table_name = self.get_config("table_name")

            if not all([token, base_id, table_name]):
                return {"status": "error", "error": "Airtable Token, Base ID, and Table Name are required."}

            headers = {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json"
            }
            action = self.get_config("action", "read_records")
            url = f"https://api.airtable.com/v0/{base_id}/{table_name}"

            async with aiohttp.ClientSession() as session:
                if action == "read_records":
                    async with session.get(url, headers=headers) as resp:
                        result = await resp.json()
                        if resp.status >= 400:
                            return {"status": "error", "error": f"Airtable Error: {result.get('error', {}).get('message')}"}
                        return {
                            "status": "success",
                            "data": {
                                "records": result.get("records", []),
                                "count": len(result.get("records", []))
                            }
                        }

                elif action == "write_record":
                    fields = input_data if isinstance(input_data, dict) else self.get_config("data", {})
                    if not fields and isinstance(input_data, str):
                        fields = {"content": input_data}
                    
                    payload = {"records": [{"fields": fields}]}
                    async with session.post(url, headers=headers, json=payload) as resp:
                        result = await resp.json()
                        if resp.status >= 400:
                             return {"status": "error", "error": f"Airtable Error: {result.get('error', {}).get('message')}"}
                        
                        created_record = result.get("records", [{}])[0]
                        return {
                            "status": "success",
                            "data": {
                                "id": created_record.get("id"),
                                "fields": created_record.get("fields")
                            }
                        }

            return {"status": "error", "error": f"Unsupported action: {action}"}

        except Exception as e:
            return {"status": "error", "error": f"Airtable Node Error: {str(e)}"}