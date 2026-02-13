"""
Clio Node - Studio Standard
Batch 67: Legal & Compliance
"""
from typing import Any, Dict, Optional, List
import aiohttp
from ...base import BaseNode
from ...registry import register_node

@register_node("clio_node")
class ClioNode(BaseNode):
    """
    Automate legal practice management and case tracking via Clio Manage API.
    """
    node_type = "clio_node"
    version = "1.0.0"
    category = "legal"
    credentials_required = ["clio_auth"]

    inputs = {
        "action": {
            "type": "dropdown",
            "default": "list_matters",
            "options": ["list_matters", "get_matter", "list_contacts", "list_activities"],
            "description": "Clio action"
        },
        "matter_id": {
            "type": "string",
            "optional": True,
            "description": "Unique ID of the legal matter"
        },
        "limit": {
            "type": "number",
            "default": 20
        }
    }

    outputs = {
        "result": {"type": "any"},
        "status": {"type": "string"},
        "count": {"type": "number"}
    }

    async def execute(self, input_data: Any, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        try:
            creds = await self.get_credential("clio_auth")
            access_token = creds.get("access_token") if creds else self.get_config("access_token")
            
            if not access_token:
                return {"status": "error", "error": "Clio Access Token is required."}

            headers = {
                "Authorization": f"Bearer {access_token}",
                "Accept": "application/json"
            }
            
            base_url = "https://app.clio.com/api/v4"
            action = self.get_config("action", "list_matters")
            limit = int(self.get_config("limit", 20))

            async with aiohttp.ClientSession() as session:
                if action == "list_matters":
                    url = f"{base_url}/matters"
                    params = {"limit": limit, "fields": "id,display_number,client{name},status"}
                    async with session.get(url, headers=headers, params=params) as resp:
                        res_data = await resp.json()
                        data = res_data.get("data", [])
                        return {"status": "success", "data": {"result": data, "count": len(data)}}

                elif action == "get_matter":
                    m_id = self.get_config("matter_id") or str(input_data)
                    url = f"{base_url}/matters/{m_id}"
                    async with session.get(url, headers=headers) as resp:
                        res_data = await resp.json()
                        return {"status": "success", "data": {"result": res_data.get("data")}}

                elif action == "list_contacts":
                    url = f"{base_url}/contacts"
                    async with session.get(url, headers=headers) as resp:
                        res_data = await resp.json()
                        data = res_data.get("data", [])
                        return {"status": "success", "data": {"result": data, "count": len(data)}}

                return {"status": "error", "error": f"Unsupported Clio action: {action}"}

        except Exception as e:
            return {"status": "error", "error": f"Clio Node Failed: {str(e)}"}
