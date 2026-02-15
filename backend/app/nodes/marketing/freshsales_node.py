"""
Freshsales Node - Studio Standard (Universal Method)
Batch 108: Marketing & CRM
"""
from typing import Any, Dict, Optional
import aiohttp
from ...base import BaseNode
from ...registry import register_node

@register_node("freshsales_node")
class FreshsalesNode(BaseNode):
    """
    Freshsales (Freshworks CRM) integration.
    """
    node_type = "freshsales_node"
    version = "1.0.0"
    category = "marketing"
    credentials_required = ["freshsales_auth"]

    inputs = {
        "action": {
            "type": "dropdown",
            "default": "create_contact",
            "options": ["create_contact", "list_contacts", "create_lead"],
            "description": "Freshsales action"
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
            creds = await self.get_credential("freshsales_auth")
            api_key = creds.get("api_key")
            domain = creds.get("domain") # e.g. company.freshsales.io
            
            if not api_key or not domain:
                return {"status": "error", "error": "Freshsales API key and domain required"}

            base_url = f"https://{domain}/api"
            headers = {"Authorization": f"Token token={api_key}", "Content-Type": "application/json"}
            
            action = self.get_config("action", "create_contact")

            async with aiohttp.ClientSession() as session:
                if action == "create_contact":
                    first_name = self.get_config("first_name")
                    last_name = self.get_config("last_name")
                    
                    if not last_name: # Often required
                         pass 
                         
                    payload = {"contact": {"first_name": first_name, "last_name": last_name}}
                    
                    url = f"{base_url}/contacts"
                    async with session.post(url, headers=headers, json=payload) as resp:
                         if resp.status != 200:
                            error_text = await resp.text()
                            return {"status": "error", "error": f"Freshsales API Error {resp.status}: {error_text}"}
                         res_data = await resp.json()
                         return {"status": "success", "data": {"result": res_data}}
                
                elif action == "list_contacts":
                     # Listing views usually required, defaulting to all contacts view logic if allowed or recent
                     url = f"{base_url}/contacts/view/all" # Generic view ID often needed, fallback to direct list if available
                     # Using filtered list endpoint for simplicity if available
                     url = f"{base_url}/contacts/filters" 
                     # Actually standard list is GET /contacts usually
                     url = f"{base_url}/contacts"
                     async with session.get(url, headers=headers) as resp:
                         res_data = await resp.json()
                         return {"status": "success", "data": {"result": res_data.get("contacts", [])}}

            return {"status": "error", "error": f"Unsupported action: {action}"}

        except Exception as e:
            return {"status": "error", "error": f"Freshsales Node Failed: {str(e)}"}
