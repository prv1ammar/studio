"""
Greenhouse Node - Studio Standard
Batch 64: HR & Recruiting
"""
from typing import Any, Dict, Optional, List
import aiohttp
import base64
from ..base import BaseNode
from ..registry import register_node

@register_node("greenhouse_node")
class GreenhouseNode(BaseNode):
    """
    Automate applicant tracking and hiring events via Greenhouse Harvest API.
    """
    node_type = "greenhouse_node"
    version = "1.0.0"
    category = "hr"
    credentials_required = ["greenhouse_auth"]


    properties = [
        {
            'displayName': 'Operation',
            'name': 'operation',
            'type': 'options',
            'default': 'list_candidates',
            'options': [
                {'name': 'List Candidates', 'value': 'list_candidates'},
                {'name': 'Get Candidate', 'value': 'get_candidate'},
                {'name': 'List Jobs', 'value': 'list_jobs'},
                {'name': 'List Applications', 'value': 'list_applications'},
            ],
            'description': 'Greenhouse action to perform',
        },
        {
            'displayName': 'Candidate Id',
            'name': 'candidate_id',
            'type': 'string',
            'default': '',
            'description': 'Unique ID of the candidate',
        },
        {
            'displayName': 'Per Page',
            'name': 'per_page',
            'type': 'string',
            'default': 100,
        },
    ]
    inputs = {
        "action": {
            "type": "dropdown",
            "default": "list_candidates",
            "options": ["list_candidates", "get_candidate", "list_jobs", "list_applications"],
            "description": "Greenhouse action to perform"
        },
        "candidate_id": {
            "type": "string",
            "optional": True,
            "description": "Unique ID of the candidate"
        },
        "per_page": {
            "type": "number",
            "default": 100
        }
    }

    outputs = {
        "result": {"type": "any"},
        "status": {"type": "string"},
        "count": {"type": "number"}
    }

    async def execute(self, input_data: Any, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        try:
            # 1. Resolve Auth
            creds = await self.get_credential("greenhouse_auth")
            api_key = creds.get("api_key") if creds else self.get_config("api_key")
            
            if not api_key:
                return {"status": "error", "error": "Greenhouse Harvest API Key is required."}

            # Greenhouse uses Basic Auth with api_key as username and empty password
            auth_str = f"{api_key}:"
            encoded_auth = base64.b64encode(auth_str.encode()).decode()
            
            headers = {
                "Authorization": f"Basic {encoded_auth}",
                "Accept": "application/json"
            }
            
            base_url = "https://harvest.greenhouse.io/v1"
            action = self.get_config("action", "list_candidates")
            per_page = int(self.get_config("per_page", 100))

            async with aiohttp.ClientSession() as session:
                if action == "list_candidates":
                    url = f"{base_url}/candidates"
                    params = {"per_page": per_page}
                    async with session.get(url, headers=headers, params=params) as resp:
                        res_data = await resp.json()
                        return {"status": "success", "data": {"result": res_data, "count": len(res_data)}}

                elif action == "get_candidate":
                    candidate_id = self.get_config("candidate_id") or str(input_data)
                    url = f"{base_url}/candidates/{candidate_id}"
                    async with session.get(url, headers=headers) as resp:
                        res_data = await resp.json()
                        return {"status": "success", "data": {"result": res_data}}

                elif action == "list_jobs":
                    url = f"{base_url}/jobs"
                    params = {"per_page": per_page}
                    async with session.get(url, headers=headers, params=params) as resp:
                        res_data = await resp.json()
                        return {"status": "success", "data": {"result": res_data, "count": len(res_data)}}

                elif action == "list_applications":
                    url = f"{base_url}/applications"
                    params = {"per_page": per_page}
                    async with session.get(url, headers=headers, params=params) as resp:
                        res_data = await resp.json()
                        return {"status": "success", "data": {"result": res_data, "count": len(res_data)}}

                return {"status": "error", "error": f"Unsupported Greenhouse action: {action}"}

        except Exception as e:
            return {"status": "error", "error": f"Greenhouse Node Failed: {str(e)}"}