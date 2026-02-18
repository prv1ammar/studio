"""
Datadog Node - Studio Standard
Batch 83: Observability & SRE
"""
from typing import Any, Dict, Optional, List
import aiohttp
import time
from ..base import BaseNode
from ..registry import register_node

@register_node("datadog_node")
class DatadogNode(BaseNode):
    """
    Fetch metrics and monitors via the Datadog API v1/v2.
    """
    node_type = "datadog_node"
    version = "1.0.0"
    category = "observability"
    credentials_required = ["datadog_auth"]


    properties = [
        {
            'displayName': 'Operation',
            'name': 'operation',
            'type': 'options',
            'default': 'list_monitors',
            'options': [
                {'name': 'List Monitors', 'value': 'list_monitors'},
                {'name': 'Query Metrics', 'value': 'query_metrics'},
                {'name': 'List Events', 'value': 'list_events'},
                {'name': 'Create Event', 'value': 'create_event'},
            ],
            'description': 'Datadog action',
        },
        {
            'displayName': 'Query',
            'name': 'query',
            'type': 'string',
            'default': '',
            'description': 'Metric query or search term',
        },
        {
            'displayName': 'Region',
            'name': 'region',
            'type': 'options',
            'default': 'us1',
            'options': [
                {'name': 'Us1', 'value': 'us1'},
                {'name': 'Us3', 'value': 'us3'},
                {'name': 'Us5', 'value': 'us5'},
                {'name': 'Eu1', 'value': 'eu1'},
                {'name': 'Us1-Fed', 'value': 'us1-fed'},
            ],
            'description': 'Datadog site region',
        },
    ]
    inputs = {
        "action": {
            "type": "dropdown",
            "default": "list_monitors",
            "options": ["list_monitors", "query_metrics", "list_events", "create_event"],
            "description": "Datadog action"
        },
        "query": {
            "type": "string",
            "optional": True,
            "description": "Metric query or search term"
        },
        "region": {
            "type": "dropdown",
            "default": "us1",
            "options": ["us1", "us3", "us5", "eu1", "us1-fed"],
            "description": "Datadog site region"
        }
    }

    outputs = {
        "result": {"type": "any"},
        "status": {"type": "string"}
    }

    async def execute(self, input_data: Any, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        try:
            creds = await self.get_credential("datadog_auth")
            api_key = creds.get("api_key") if creds else self.get_config("api_key")
            app_key = creds.get("application_key") if creds else self.get_config("application_key")
            
            if not api_key or not app_key:
                return {"status": "error", "error": "Datadog API Key and Application Key are required."}

            headers = {
                "DD-API-KEY": api_key,
                "DD-APPLICATION-KEY": app_key,
                "Accept": "application/json"
            }
            
            region = self.get_config("region", "us1")
            base_urls = {
                "us1": "https://api.datadoghq.com",
                "us3": "https://api.us3.datadoghq.com",
                "us5": "https://api.us5.datadoghq.com",
                "eu1": "https://api.datadoghq.eu",
                "us1-fed": "https://api.ddog-gov.com"
            }
            base_url = base_urls.get(region, "https://api.datadoghq.com")
            action = self.get_config("action", "list_monitors")

            async with aiohttp.ClientSession() as session:
                if action == "list_monitors":
                    url = f"{base_url}/api/v1/monitor"
                    async with session.get(url, headers=headers) as resp:
                        res_data = await resp.json()
                        return {"status": "success", "data": {"result": res_data}}

                elif action == "query_metrics":
                    query = self.get_config("query") or str(input_data)
                    now = int(time.time())
                    url = f"{base_url}/api/v1/query"
                    params = {"from": now - 3600, "to": now, "query": query}
                    async with session.get(url, headers=headers, params=params) as resp:
                        res_data = await resp.json()
                        return {"status": "success", "data": {"result": res_data}}

                elif action == "list_events":
                    now = int(time.time())
                    url = f"{base_url}/api/v1/events"
                    params = {"start": now - 3600, "end": now}
                    async with session.get(url, headers=headers, params=params) as resp:
                        res_data = await resp.json()
                        return {"status": "success", "data": {"result": res_data.get("events", [])}}

                return {"status": "error", "error": f"Unsupported action: {action}"}

        except Exception as e:
            return {"status": "error", "error": f"Datadog Node Failed: {str(e)}"}