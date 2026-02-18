"""
Splunk Node - Studio Standard
Batch 83: Observability & SRE
"""
from typing import Any, Dict, Optional, List
import aiohttp
from ..base import BaseNode
from ..registry import register_node

@register_node("splunk_node")
class SplunkNode(BaseNode):
    """
    Search log data and security events via the Splunk HEC or Management API.
    """
    node_type = "splunk_node"
    version = "1.0.0"
    category = "observability"
    credentials_required = ["splunk_auth"]


    properties = [
        {
            'displayName': 'Operation',
            'name': 'operation',
            'type': 'options',
            'default': 'search_logs',
            'options': [
                {'name': 'Search Logs', 'value': 'search_logs'},
                {'name': 'List Indexes', 'value': 'list_indexes'},
                {'name': 'Send Hec Event', 'value': 'send_hec_event'},
            ],
            'description': 'Splunk action',
        },
        {
            'displayName': 'Base Url',
            'name': 'base_url',
            'type': 'string',
            'default': '',
            'description': 'Splunk Management API URL (e.g. https://splunk.example.com:8089)',
            'required': True,
        },
        {
            'displayName': 'Query',
            'name': 'query',
            'type': 'string',
            'default': '',
            'description': 'Splunk search query (e.g. 'search index=_internal | head 10')',
        },
    ]
    inputs = {
        "action": {
            "type": "dropdown",
            "default": "search_logs",
            "options": ["search_logs", "list_indexes", "send_hec_event"],
            "description": "Splunk action"
        },
        "query": {
            "type": "string",
            "optional": True,
            "description": "Splunk search query (e.g. 'search index=_internal | head 10')"
        },
        "base_url": {
            "type": "string",
            "required": True,
            "description": "Splunk Management API URL (e.g. https://splunk.example.com:8089)"
        }
    }

    outputs = {
        "result": {"type": "any"},
        "status": {"type": "string"}
    }

    async def execute(self, input_data: Any, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        try:
            creds = await self.get_credential("splunk_auth")
            token = creds.get("token") or creds.get("api_key")
            user = creds.get("username")
            password = creds.get("password")
            
            headers = {"Accept": "application/json"}
            if token:
                headers["Authorization"] = f"Splunk {token}"
            elif user and password:
                import base64
                auth = base64.b64encode(f"{user}:{password}".encode()).decode()
                headers["Authorization"] = f"Basic {auth}"
            else:
                return {"status": "error", "error": "Splunk Credentials required."}

            base_url = self.get_config("base_url").rstrip("/")
            action = self.get_config("action", "search_logs")

            async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(ssl=False)) as session:
                if action == "list_indexes":
                    url = f"{base_url}/services/data/indexes?output_mode=json"
                    async with session.get(url, headers=headers) as resp:
                        res_data = await resp.json()
                        return {"status": "success", "data": {"result": res_data.get("entry", [])}}

                elif action == "search_logs":
                    query = self.get_config("query") or str(input_data)
                    url = f"{base_url}/services/search/jobs/export"
                    data = {"search": query, "output_mode": "json"}
                    async with session.post(url, headers=headers, data=data) as resp:
                        # Export returns newline-delimited JSON or a stream
                        res_text = await resp.text()
                        return {"status": "success", "data": {"result": res_text}}

                return {"status": "error", "error": f"Unsupported action: {action}"}
        except Exception as e:
            return {"status": "error", "error": f"Splunk Node Failed: {str(e)}"}