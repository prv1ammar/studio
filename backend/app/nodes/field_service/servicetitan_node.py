"""
ServiceTitan Node - Studio Standard
Batch 80: Industrial & Service Ops
"""
from typing import Any, Dict, Optional, List
import aiohttp
from ..base import BaseNode
from ..registry import register_node

@register_node("servicetitan_node")
class ServiceTitanNode(BaseNode):
    """
    Orchestrate field service jobs and technician tracking via ServiceTitan API.
    """
    node_type = "servicetitan_node"
    version = "1.0.0"
    category = "field_service"
    credentials_required = ["servicetitan_auth"]


    properties = [
        {
            'displayName': 'Operation',
            'name': 'operation',
            'type': 'options',
            'default': 'list_jobs',
            'options': [
                {'name': 'List Jobs', 'value': 'list_jobs'},
                {'name': 'Get Job', 'value': 'get_job'},
                {'name': 'List Technicians', 'value': 'list_technicians'},
                {'name': 'Get Technician Location', 'value': 'get_technician_location'},
            ],
            'description': 'ServiceTitan action',
        },
        {
            'displayName': 'Tenant Id',
            'name': 'tenant_id',
            'type': 'string',
            'default': '',
            'required': True,
        },
    ]
    inputs = {
        "action": {
            "type": "dropdown",
            "default": "list_jobs",
            "options": ["list_jobs", "get_job", "list_technicians", "get_technician_location"],
            "description": "ServiceTitan action"
        },
        "tenant_id": {
            "type": "string",
            "required": True
        }
    }

    outputs = {
        "result": {"type": "any"},
        "status": {"type": "string"}
    }

    async def execute(self, input_data: Any, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        try:
            creds = await self.get_credential("servicetitan_auth")
            api_key = creds.get("api_key") if creds else self.get_config("api_key")
            
            if not api_key:
                return {"status": "error", "error": "ServiceTitan API Key is required."}

            headers = {"Authorization": api_key, "ST-Tenant-Id": self.get_config("tenant_id")}
            base_url = "https://api.servicetitan.io/v2"
            action = self.get_config("action", "list_jobs")

            async with aiohttp.ClientSession() as session:
                if action == "list_jobs":
                    url = f"{base_url}/jcm/v2/jobs"
                    async with session.get(url, headers=headers) as resp:
                        res_data = await resp.json()
                        return {"status": "success", "data": {"result": res_data}}
                
                return {"status": "error", "error": f"Unsupported action: {action}"}
        except Exception as e:
            return {"status": "error", "error": f"ServiceTitan Node Failed: {str(e)}"}