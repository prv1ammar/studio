"""
Copper Node - Studio Standard (Universal Method)
Batch 108: Marketing & CRM
"""
from typing import Any, Dict, Optional
import aiohttp
from ...base import BaseNode
from ...registry import register_node

@register_node("copper_node")
class CopperNode(BaseNode):
    """
    Copper CRM integration (ProsperWorks).
    """
    node_type = "copper_node"
    version = "1.0.0"
    category = "marketing"
    credentials_required = ["copper_auth"]

    inputs = {
        "action": {
            "type": "dropdown",
            "default": "create_person",
            "options": ["create_person", "create_lead", "create_opportunity", "search"],
            "description": "Copper action"
        },
        "name": {
            "type": "string",
            "optional": True
        },
        "email": {
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
            creds = await self.get_credential("copper_auth")
            api_key = creds.get("api_key")
            email = creds.get("email") # Copper requires email + token for auth headers
            
            if not api_key or not email:
                return {"status": "error", "error": "Copper API key and account email required"}

            base_url = "https://api.copper.com/developer_api/v1"
            headers = {
                "X-PW-AccessToken": api_key,
                "X-PW-Application": "developer_api",
                "X-PW-UserEmail": email,
                "Content-Type": "application/json"
            }
            
            action = self.get_config("action", "create_person")

            async with aiohttp.ClientSession() as session:
                if action == "create_person":
                    name = self.get_config("name")
                    contact_email = self.get_config("email")
                    
                    if not name:
                        return {"status": "error", "error": "name required"}
                        
                    payload = {"name": name}
                    if contact_email:
                        payload["emails"] = [{"email": contact_email, "category": "work"}]
                        
                    url = f"{base_url}/people"
                    async with session.post(url, headers=headers, json=payload) as resp:
                         if resp.status != 200:
                            error_text = await resp.text()
                            return {"status": "error", "error": f"Copper API Error {resp.status}: {error_text}"}
                         res_data = await resp.json()
                         return {"status": "success", "data": {"result": res_data}}

                elif action == "create_lead":
                    name = self.get_config("name")
                    if not name: return {"status": "error", "error": "name required"}
                    payload = {"name": name}
                    url = f"{base_url}/leads"
                    async with session.post(url, headers=headers, json=payload) as resp:
                         res_data = await resp.json()
                         return {"status": "success", "data": {"result": res_data}}

            return {"status": "error", "error": f"Unsupported action: {action}"}

        except Exception as e:
            return {"status": "error", "error": f"Copper Node Failed: {str(e)}"}
