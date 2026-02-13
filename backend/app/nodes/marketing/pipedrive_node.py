import aiohttp
from typing import Any, Dict, Optional, List
from ..base import BaseNode
from ..registry import register_node

@register_node("pipedrive_crm")
class PipedriveNode(BaseNode):
    """
    Automate Pipedrive CRM actions (Persons, Deals, etc.).
    """
    node_type = "pipedrive_crm"
    version = "1.0.0"
    category = "integrations"
    credentials_required = ["pipedrive_auth"]

    inputs = {
        "action": {"type": "string", "default": "create_person", "enum": ["create_person", "create_deal"]},
        "company_domain": {"type": "string", "description": "Pipedrive company domain"},
        "data": {"type": "object", "optional": True}
    }
    outputs = {
        "id": {"type": "number"},
        "status": {"type": "string"}
    }

    async def execute(self, input_data: Any, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        try:
            # 1. Resolve Auth
            creds = await self.get_credential("pipedrive_auth")
            token = creds.get("api_token") if creds else self.get_config("api_token")
            domain = self.get_config("company_domain") or (creds.get("domain") if creds else None)
            
            if not token or not domain:
                return {"status": "error", "error": "Pipedrive API Token and Company Domain are required."}

            action = self.get_config("action", "create_person")
            base_url = f"https://{domain}.pipedrive.com/api/v1"
            
            async with aiohttp.ClientSession() as session:
                if action == "create_person":
                    url = f"{base_url}/persons?api_token={token}"
                    payload = input_data if isinstance(input_data, dict) else self.get_config("data", {})
                    if not payload and isinstance(input_data, str):
                        payload = {"name": input_data}
                elif action == "create_deal":
                    url = f"{base_url}/deals?api_token={token}"
                    payload = input_data if isinstance(input_data, dict) else self.get_config("data", {})
                    if not payload and isinstance(input_data, str):
                        payload = {"title": input_data}
                else:
                    return {"status": "error", "error": f"Unsupported action: {action}"}

                async with session.post(url, json=payload) as resp:
                    result = await resp.json()
                    if not result.get("success"):
                         return {"status": "error", "error": f"Pipedrive Error: {result.get('error')}"}
                    
                    return {
                        "status": "success",
                        "data": {
                            "id": result["data"]["id"],
                            "type": action
                        }
                    }

        except Exception as e:
            return {"status": "error", "error": f"Pipedrive Node Error: {str(e)}"}
