"""
Ironclad Node - Studio Standard
Batch 67: Legal & Compliance
"""
from typing import Any, Dict, Optional, List
import aiohttp
from ...base import BaseNode
from ...registry import register_node

@register_node("ironclad_node")
class IroncladNode(BaseNode):
    """
    Automate contract lifecycle management (CLM) via Ironclad API.
    """
    node_type = "ironclad_node"
    version = "1.0.0"
    category = "legal"
    credentials_required = ["ironclad_auth"]

    inputs = {
        "action": {
            "type": "dropdown",
            "default": "list_workflows",
            "options": ["list_workflows", "get_workflow", "list_records", "get_record"],
            "description": "Ironclad action"
        },
        "workflow_id": {
            "type": "string",
            "optional": True
        },
        "record_id": {
            "type": "string",
            "optional": True
        }
    }

    outputs = {
        "result": {"type": "any"},
        "status": {"type": "string"},
        "count": {"type": "number"}
    }

    async def execute(self, input_data: Any, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        try:
            creds = await self.get_credential("ironclad_auth")
            api_key = creds.get("api_key") if creds else self.get_config("api_key")
            
            if not api_key:
                return {"status": "error", "error": "Ironclad API Key is required."}

            headers = {
                "Authorization": f"Bearer {api_key}",
                "Accept": "application/json",
                "Content-Type": "application/json"
            }
            
            base_url = "https://ironcladapp.com/api/v1"
            action = self.get_config("action", "list_workflows")

            async with aiohttp.ClientSession() as session:
                if action == "list_workflows":
                    url = f"{base_url}/workflows"
                    async with session.get(url, headers=headers) as resp:
                        res_data = await resp.json()
                        workflows = res_data.get("data", [])
                        return {"status": "success", "data": {"result": workflows, "count": len(workflows)}}

                elif action == "get_workflow":
                    w_id = self.get_config("workflow_id") or str(input_data)
                    url = f"{base_url}/workflows/{w_id}"
                    async with session.get(url, headers=headers) as resp:
                        res_data = await resp.json()
                        return {"status": "success", "data": {"result": res_data}}

                elif action == "list_records":
                    url = f"{base_url}/records"
                    async with session.get(url, headers=headers) as resp:
                        res_data = await resp.json()
                        records = res_data.get("data", [])
                        return {"status": "success", "data": {"result": records, "count": len(records)}}

                return {"status": "error", "error": f"Unsupported Ironclad action: {action}"}

        except Exception as e:
            return {"status": "error", "error": f"Ironclad Node Failed: {str(e)}"}
