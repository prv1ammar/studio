"""
ServiceNow Node - Studio Standard (Universal Method)
Batch 97: Support & Ticketing (Deepening Parity)
"""
from typing import Any, Dict, Optional, List
import aiohttp
import base64
from ..base import BaseNode
from ..registry import register_node

@register_node("servicenow_node")
class ServiceNowNode(BaseNode):
    """
    Manage incidents and records via ServiceNow REST API (Table API).
    """
    node_type = "servicenow_node"
    version = "1.0.0"
    category = "support"
    credentials_required = ["servicenow_auth"]


    properties = [
        {
            'displayName': 'Operation',
            'name': 'operation',
            'type': 'options',
            'default': 'list_incidents',
            'options': [
                {'name': 'List Incidents', 'value': 'list_incidents'},
                {'name': 'Get Record', 'value': 'get_record'},
                {'name': 'Create Incident', 'value': 'create_incident'},
                {'name': 'Update Record', 'value': 'update_record'},
                {'name': 'Delete Record', 'value': 'delete_record'},
            ],
            'description': 'ServiceNow action',
        },
        {
            'displayName': 'Data',
            'name': 'data',
            'type': 'string',
            'default': '',
            'description': 'JSON body for create/update',
        },
        {
            'displayName': 'Query',
            'name': 'query',
            'type': 'string',
            'default': '',
            'description': 'Encoded query string (sysparm_query)',
        },
        {
            'displayName': 'Sys Id',
            'name': 'sys_id',
            'type': 'string',
            'default': '',
            'description': 'Record System ID',
        },
        {
            'displayName': 'Table',
            'name': 'table',
            'type': 'string',
            'default': 'incident',
            'description': 'Table name (e.g. incident, problem, change_request)',
        },
    ]
    inputs = {
        "action": {
            "type": "dropdown",
            "default": "list_incidents",
            "options": ["list_incidents", "get_record", "create_incident", "update_record", "delete_record"],
            "description": "ServiceNow action"
        },
        "table": {
            "type": "string",
            "default": "incident",
            "description": "Table name (e.g. incident, problem, change_request)"
        },
        "sys_id": {
            "type": "string",
            "optional": True,
            "description": "Record System ID"
        },
        "query": {
            "type": "string",
            "optional": True,
            "description": "Encoded query string (sysparm_query)"
        },
        "data": {
            "type": "string",
            "optional": True,
            "description": "JSON body for create/update"
        }
    }

    outputs = {
        "result": {"type": "any"},
        "status": {"type": "string"}
    }

    async def execute(self, input_data: Any, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        try:
            # 1. Authentication
            creds = await self.get_credential("servicenow_auth")
            instance = creds.get("instance") # e.g. dev12345.service-now.com
            username = creds.get("username")
            password = creds.get("password")
            
            if not instance or not username or not password:
                return {"status": "error", "error": "ServiceNow Instance, User, and Password required."}

            # Basic Auth
            auth_str = f"{username}:{password}"
            b64_auth = base64.b64encode(auth_str.encode()).decode()
            
            headers = {
                "Authorization": f"Basic {b64_auth}",
                "Content-Type": "application/json",
                "Accept": "application/json"
            }
            
            # Canonicalize instance
            if not instance.startswith("http"):
                base_url = f"https://{instance}/api/now/table"
            else:
                base_url = f"{instance.rstrip('/')}/api/now/table"

            action = self.get_config("action", "list_incidents")
            table = self.get_config("table", "incident")

            async with aiohttp.ClientSession() as session:
                if action == "list_incidents" or action == "list_records": # Generalized
                    url = f"{base_url}/{table}"
                    params = {"sysparm_limit": 10}
                    if self.get_config("query"):
                        params["sysparm_query"] = self.get_config("query")
                        
                    async with session.get(url, headers=headers, params=params) as resp:
                        if resp.status != 200:
                            return {"status": "error", "error": f"ServiceNow API Error: {resp.status}"}
                        res_data = await resp.json()
                        return {"status": "success", "data": {"result": res_data.get("result", [])}}

                elif action == "get_record":
                    sys_id = self.get_config("sys_id") or str(input_data)
                    url = f"{base_url}/{table}/{sys_id}"
                    async with session.get(url, headers=headers) as resp:
                        if resp.status != 200:
                            return {"status": "error", "error": f"ServiceNow API Error: {resp.status}"}
                        res_data = await resp.json()
                        return {"status": "success", "data": {"result": res_data.get("result", {})}}

                elif action == "create_incident": # Or generic create record
                    data_str = self.get_config("data") or "{}"
                    import json
                    try:
                        payload = json.loads(data_str) if isinstance(data_str, str) else data_str
                    except:
                        payload = {}
                    
                    # Ensure minimal fields if incident
                    if table == "incident" and "short_description" not in payload:
                        payload["short_description"] = "Created from Studio"

                    url = f"{base_url}/{table}"
                    async with session.post(url, headers=headers, json=payload) as resp:
                        if resp.status != 201:
                            return {"status": "error", "error": f"ServiceNow API Error: {resp.status}"}
                        res_data = await resp.json()
                        return {"status": "success", "data": {"result": res_data.get("result", {})}}

                elif action == "update_record":
                    sys_id = self.get_config("sys_id")
                    if not sys_id: return {"status": "error", "error": "sys_id required"}
                    
                    data_str = self.get_config("data")
                    import json
                    payload = json.loads(data_str) if isinstance(data_str, str) else data_str

                    url = f"{base_url}/{table}/{sys_id}"
                    async with session.put(url, headers=headers, json=payload) as resp:
                         if resp.status != 200:
                            return {"status": "error", "error": f"ServiceNow API Error: {resp.status}"}
                         res_data = await resp.json()
                         return {"status": "success", "data": {"result": res_data.get("result", {})}}

                elif action == "delete_record":
                    sys_id = self.get_config("sys_id")
                    if not sys_id: return {"status": "error", "error": "sys_id required"}
                    
                    url = f"{base_url}/{table}/{sys_id}"
                    async with session.delete(url, headers=headers) as resp:
                        if resp.status != 204:
                            return {"status": "error", "error": f"ServiceNow API Error: {resp.status}"}
                        return {"status": "success", "data": {"result": {"message": "Record deleted"}}}

                return {"status": "error", "error": f"Unsupported action: {action}"}

        except Exception as e:
            return {"status": "error", "error": f"ServiceNow Node Failed: {str(e)}"}