"""
Procore Node - Studio Standard
Batch 80: Industrial & Service Ops
"""
from typing import Any, Dict, Optional, List
import aiohttp
from ...base import BaseNode
from ...registry import register_node

@register_node("procore_node")
class ProcoreNode(BaseNode):
    """
    Manage construction projects, RFIs, and submittals via Procore API.
    """
    node_type = "procore_node"
    version = "1.0.0"
    category = "construction"
    credentials_required = ["procore_auth"]

    inputs = {
        "action": {
            "type": "dropdown",
            "default": "list_projects",
            "options": ["list_projects", "get_project", "list_rfis", "create_rfi"],
            "description": "Procore action"
        },
        "company_id": {
            "type": "string",
            "required": True
        },
        "project_id": {
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
            creds = await self.get_credential("procore_auth")
            access_token = creds.get("access_token") if creds else self.get_config("access_token")
            
            if not access_token:
                return {"status": "error", "error": "Procore Access Token is required."}

            headers = {"Authorization": f"Bearer {access_token}", "Accept": "application/json"}
            base_url = "https://api.procore.com/rest/v1.0"
            action = self.get_config("action", "list_projects")
            company_id = self.get_config("company_id")

            async with aiohttp.ClientSession() as session:
                if action == "list_projects":
                    url = f"{base_url}/projects"
                    params = {"company_id": company_id}
                    async with session.get(url, headers=headers, params=params) as resp:
                        res_data = await resp.json()
                        return {"status": "success", "data": {"result": res_data}}

                elif action == "list_rfis":
                    p_id = self.get_config("project_id") or str(input_data)
                    url = f"{base_url}/projects/{p_id}/rfis"
                    async with session.get(url, headers=headers) as resp:
                        res_data = await resp.json()
                        return {"status": "success", "data": {"result": res_data}}

                return {"status": "error", "error": f"Unsupported action: {action}"}
        except Exception as e:
            return {"status": "error", "error": f"Procore Node Failed: {str(e)}"}
