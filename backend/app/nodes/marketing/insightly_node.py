"""
Insightly Node - Studio Standard (Universal Method)
Batch 108: Marketing & CRM
"""
from typing import Any, Dict, Optional
import aiohttp
from ...base import BaseNode
from ...registry import register_node

@register_node("insightly_node")
class InsightlyNode(BaseNode):
    """
    Insightly CRM integration.
    """
    node_type = "insightly_node"
    version = "1.0.0"
    category = "marketing"
    credentials_required = ["insightly_auth"]

    inputs = {
        "action": {
            "type": "dropdown",
            "default": "create_contact",
            "options": ["create_contact", "list_contacts", "create_lead"],
            "description": "Insightly action"
        },
        "first_name": {
            "type": "string",
            "optional": True
        },
        "last_name": {
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
            creds = await self.get_credential("insightly_auth")
            api_key = creds.get("api_key")
            api_url = creds.get("api_url", "https://api.insightly.com/v3.1")
            
            if not api_key:
                return {"status": "error", "error": "Insightly API key required"}

            auth = aiohttp.BasicAuth(api_key, "")
            
            action = self.get_config("action", "create_contact")

            async with aiohttp.ClientSession() as session:
                if action == "create_contact":
                    first_name = self.get_config("first_name")
                    last_name = self.get_config("last_name")
                    
                    if not last_name: # Often required
                         return {"status": "error", "error": "last_name required"}
                         
                    payload = {"FIRST_NAME": first_name, "LAST_NAME": last_name}
                    
                    url = f"{api_url}/Contacts"
                    async with session.post(url, auth=auth, json=payload) as resp:
                         if resp.status != 201:
                            error_text = await resp.text()
                            return {"status": "error", "error": f"Insightly API Error {resp.status}: {error_text}"}
                         res_data = await resp.json()
                         return {"status": "success", "data": {"result": res_data}}
                
                elif action == "list_contacts":
                     url = f"{api_url}/Contacts"
                     async with session.get(url, auth=auth) as resp:
                         res_data = await resp.json()
                         return {"status": "success", "data": {"result": res_data}}

                elif action == "create_lead":
                    first_name = self.get_config("first_name")
                    last_name = self.get_config("last_name")
                    if not last_name: return {"status": "error", "error": "last_name required"}
                    payload = {"FIRST_NAME": first_name, "LAST_NAME": last_name}
                    url = f"{api_url}/Leads"
                    async with session.post(url, auth=auth, json=payload) as resp:
                        res_data = await resp.json()
                        return {"status": "success", "data": {"result": res_data}}

            return {"status": "error", "error": f"Unsupported action: {action}"}

        except Exception as e:
            return {"status": "error", "error": f"Insightly Node Failed: {str(e)}"}
