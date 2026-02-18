"""
Terraform Node - Studio Standard
Batch 82: Agile & DevOps
"""
from typing import Any, Dict, Optional, List
import aiohttp
from ..base import BaseNode
from ..registry import register_node

@register_node("terraform_node")
class TerraformNode(BaseNode):
    """
    Manage infrastructure as code via Terraform Cloud/Enterprise API.
    """
    node_type = "terraform_node"
    version = "1.0.0"
    category = "devops"
    credentials_required = ["terraform_auth"]


    properties = [
        {
            'displayName': 'Operation',
            'name': 'operation',
            'type': 'options',
            'default': 'list_workspaces',
            'options': [
                {'name': 'List Workspaces', 'value': 'list_workspaces'},
                {'name': 'Get Workspace', 'value': 'get_workspace'},
                {'name': 'Create Run', 'value': 'create_run'},
                {'name': 'List Runs', 'value': 'list_runs'},
            ],
            'description': 'Terraform action',
        },
        {
            'displayName': 'Organization',
            'name': 'organization',
            'type': 'string',
            'default': '',
            'description': 'Terraform organization name',
            'required': True,
        },
        {
            'displayName': 'Workspace Id',
            'name': 'workspace_id',
            'type': 'string',
            'default': '',
        },
    ]
    inputs = {
        "action": {
            "type": "dropdown",
            "default": "list_workspaces",
            "options": ["list_workspaces", "get_workspace", "create_run", "list_runs"],
            "description": "Terraform action"
        },
        "organization": {
            "type": "string",
            "required": True,
            "description": "Terraform organization name"
        },
        "workspace_id": {
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
            creds = await self.get_credential("terraform_auth")
            token = creds.get("token") if creds else self.get_config("token")
            
            if not token:
                return {"status": "error", "error": "Terraform API Token is required."}

            headers = {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/vnd.api+json"
            }
            
            base_url = "https://app.terraform.io/api/v2"
            action = self.get_config("action", "list_workspaces")
            org = self.get_config("organization")

            async with aiohttp.ClientSession() as session:
                if action == "list_workspaces":
                    url = f"{base_url}/organizations/{org}/workspaces"
                    async with session.get(url, headers=headers) as resp:
                        res_data = await resp.json()
                        return {"status": "success", "data": {"result": res_data.get("data", [])}}

                elif action == "create_run":
                    ws_id = self.get_config("workspace_id") or str(input_data)
                    url = f"{base_url}/runs"
                    payload = {
                        "data": {
                            "attributes": {"is-destroy": False},
                            "relationships": {
                                "workspace": {"data": {"type": "workspaces", "id": ws_id}}
                            }
                        }
                    }
                    async with session.post(url, headers=headers, json=payload) as resp:
                        res_data = await resp.json()
                        return {"status": "success", "data": {"result": res_data.get("data", {})}}

                return {"status": "error", "error": f"Unsupported action: {action}"}

        except Exception as e:
            return {"status": "error", "error": f"Terraform Node Failed: {str(e)}"}