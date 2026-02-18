"""
Coda Node - Studio Standard
Batch 113: Productivity & Docs
"""
from typing import Any, Dict, Optional
import aiohttp
from ..base import BaseNode
from ..registry import register_node

@register_node("coda_node")
class CodaNode(BaseNode):
    """
    Interact with Coda docs, tables, and rows.
    """
    node_type = "coda_node"
    version = "1.0.0"
    category = "productivity"
    credentials_required = ["coda_auth"]


    properties = [
        {
            'displayName': 'Operation',
            'name': 'operation',
            'type': 'options',
            'default': 'list_docs',
            'options': [
                {'name': 'List Docs', 'value': 'list_docs'},
                {'name': 'Get Doc', 'value': 'get_doc'},
                {'name': 'List Tables', 'value': 'list_tables'},
                {'name': 'List Rows', 'value': 'list_rows'},
                {'name': 'Insert Row', 'value': 'insert_row'},
                {'name': 'Update Row', 'value': 'update_row'},
            ],
            'description': 'Coda action',
        },
        {
            'displayName': 'Doc Id',
            'name': 'doc_id',
            'type': 'string',
            'default': '',
            'description': 'Coda Doc ID',
        },
        {
            'displayName': 'Payload',
            'name': 'payload',
            'type': 'string',
            'default': '',
            'description': 'JSON for row data/updates',
        },
        {
            'displayName': 'Row Id',
            'name': 'row_id',
            'type': 'string',
            'default': '',
        },
        {
            'displayName': 'Table Id',
            'name': 'table_id',
            'type': 'string',
            'default': '',
            'description': 'Table ID or Name',
        },
    ]
    inputs = {
        "action": {
            "type": "dropdown",
            "default": "list_docs",
            "options": ["list_docs", "get_doc", "list_tables", "list_rows", "insert_row", "update_row"],
            "description": "Coda action"
        },
        "doc_id": {
            "type": "string",
            "optional": True,
            "description": "Coda Doc ID"
        },
        "table_id": {
            "type": "string",
            "optional": True,
            "description": "Table ID or Name"
        },
        "row_id": {
            "type": "string",
            "optional": True
        },
        "payload": {
            "type": "string",
            "optional": True,
            "description": "JSON for row data/updates"
        }
    }

    outputs = {
        "result": {"type": "any"},
        "status": {"type": "string"}
    }

    async def execute(self, input_data: Any, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        try:
            creds = await self.get_credential("coda_auth")
            api_token = creds.get("api_key") or creds.get("token")
            
            if not api_token:
                return {"status": "error", "error": "Coda API Token required"}

            headers = {
                "Authorization": f"Bearer {api_token}",
                "Content-Type": "application/json"
            }
            
            action = self.get_config("action", "list_docs")
            base_url = "https://coda.io/apis/v1"

            async with aiohttp.ClientSession() as session:
                if action == "list_docs":
                    url = f"{base_url}/docs"
                    async with session.get(url, headers=headers) as resp:
                        res_data = await resp.json()
                        return {"status": "success", "data": {"result": res_data.get("items", [])}}

                elif action == "get_doc":
                    doc_id = self.get_config("doc_id") or str(input_data)
                    url = f"{base_url}/docs/{doc_id}"
                    async with session.get(url, headers=headers) as resp:
                        res_data = await resp.json()
                        return {"status": "success", "data": {"result": res_data}}

                elif action == "list_tables":
                    doc_id = self.get_config("doc_id")
                    if not doc_id: return {"status": "error", "error": "doc_id required"}
                    url = f"{base_url}/docs/{doc_id}/tables"
                    async with session.get(url, headers=headers) as resp:
                        res_data = await resp.json()
                        return {"status": "success", "data": {"result": res_data.get("items", [])}}

                elif action == "list_rows":
                    doc_id = self.get_config("doc_id")
                    table_id = self.get_config("table_id")
                    if not doc_id or not table_id: return {"status": "error", "error": "doc_id and table_id required"}
                    url = f"{base_url}/docs/{doc_id}/tables/{table_id}/rows"
                    async with session.get(url, headers=headers) as resp:
                        res_data = await resp.json()
                        return {"status": "success", "data": {"result": res_data.get("items", [])}}

                elif action == "insert_row":
                    doc_id = self.get_config("doc_id")
                    table_id = self.get_config("table_id")
                    if not doc_id or not table_id: return {"status": "error", "error": "doc_id and table_id required"}
                    
                    row_data_str = self.get_config("payload") or str(input_data)
                    import json
                    try:
                        cells = json.loads(row_data_str)
                    except:
                        cells = input_data if isinstance(input_data, dict) else {}
                    
                    payload = {"rows": [{"cells": [{"column": k, "value": v} for k, v in cells.items()]}]}
                    
                    url = f"{base_url}/docs/{doc_id}/tables/{table_id}/rows"
                    async with session.post(url, headers=headers, json=payload) as resp:
                        if resp.status >= 400:
                            return {"status": "error", "error": f"Coda Error: {await resp.text()}"}
                        return {"status": "success", "data": {"result": "Row(s) inserted"}}

            return {"status": "error", "error": f"Unsupported action: {action}"}

        except Exception as e:
            return {"status": "error", "error": f"Coda Node Failed: {str(e)}"}