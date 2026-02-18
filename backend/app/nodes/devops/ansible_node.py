"""
Ansible Node - Studio Standard
Batch 82: Agile & DevOps
"""
from typing import Any, Dict, Optional, List
import aiohttp
from ..base import BaseNode
from ..registry import register_node

@register_node("ansible_node")
class AnsibleNode(BaseNode):
    """
    Manage configuration automation via Ansible Tower / AWX API.
    """
    node_type = "ansible_node"
    version = "1.0.0"
    category = "devops"
    credentials_required = ["ansible_auth"]


    properties = [
        {
            'displayName': 'Operation',
            'name': 'operation',
            'type': 'options',
            'default': 'list_jobs',
            'options': [
                {'name': 'List Jobs', 'value': 'list_jobs'},
                {'name': 'Launch Job', 'value': 'launch_job'},
                {'name': 'Get Job Status', 'value': 'get_job_status'},
            ],
            'description': 'Ansible action',
        },
        {
            'displayName': 'Base Url',
            'name': 'base_url',
            'type': 'string',
            'default': '',
            'description': 'AWX/Tower base URL (e.g., https://awx.example.com)',
            'required': True,
        },
        {
            'displayName': 'Job Template Id',
            'name': 'job_template_id',
            'type': 'string',
            'default': '',
        },
    ]
    inputs = {
        "action": {
            "type": "dropdown",
            "default": "list_jobs",
            "options": ["list_jobs", "launch_job", "get_job_status"],
            "description": "Ansible action"
        },
        "base_url": {
            "type": "string",
            "required": True,
            "description": "AWX/Tower base URL (e.g., https://awx.example.com)"
        },
        "job_template_id": {
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
            creds = await self.get_credential("ansible_auth")
            token = creds.get("token") if creds else self.get_config("token")
            
            if not token:
                return {"status": "error", "error": "Ansible API Token is required."}

            headers = {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json"
            }
            
            base_url = self.get_config("base_url").rstrip('/')
            action = self.get_config("action", "list_jobs")

            async with aiohttp.ClientSession() as session:
                if action == "list_jobs":
                    url = f"{base_url}/api/v2/jobs/"
                    async with session.get(url, headers=headers) as resp:
                        res_data = await resp.json()
                        return {"status": "success", "data": {"result": res_data.get("results", [])}}

                elif action == "launch_job":
                    template_id = self.get_config("job_template_id") or str(input_data)
                    url = f"{base_url}/api/v2/job_templates/{template_id}/launch/"
                    async with session.post(url, headers=headers) as resp:
                        res_data = await resp.json()
                        return {"status": "success", "data": {"result": res_data}}

                return {"status": "error", "error": f"Unsupported action: {action}"}

        except Exception as e:
            return {"status": "error", "error": f"Ansible Node Failed: {str(e)}"}