"""
Intercom Node - Studio Standard (Universal Method)
Batch 109: Analytics & Support
"""
from typing import Any, Dict, Optional
import aiohttp
from ...base import BaseNode
from ...registry import register_node

@register_node("intercom_node")
class IntercomNode(BaseNode):
    """
    Intercom integration for customer messaging.
    """
    node_type = "intercom_node"
    version = "1.0.0"
    category = "support"
    credentials_required = ["intercom_auth"]

    inputs = {
        "action": {
            "type": "dropdown",
            "default": "create_contact",
            "options": ["create_contact", "list_contacts", "send_message", "get_conversation"],
            "description": "Intercom action"
        },
        "email": {
            "type": "string",
            "optional": True
        },
        "body": {
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
            creds = await self.get_credential("intercom_auth")
            access_token = creds.get("access_token")
            
            if not access_token:
                return {"status": "error", "error": "Intercom access token required"}

            base_url = "https://api.intercom.io"
            headers = {
                "Authorization": f"Bearer {access_token}",
                "Accept": "application/json",
                "Content-Type": "application/json"
            }
            
            action = self.get_config("action", "create_contact")

            async with aiohttp.ClientSession() as session:
                if action == "create_contact":
                    email = self.get_config("email")
                    
                    if not email:
                         # Email often used as unique ID
                         pass
                    
                    payload = {"role": "user", "email": email}
                    
                    url = f"{base_url}/contacts"
                    async with session.post(url, headers=headers, json=payload) as resp:
                         if resp.status != 200:
                            error_text = await resp.text()
                            return {"status": "error", "error": f"Intercom API Error {resp.status}: {error_text}"}
                         res_data = await resp.json()
                         return {"status": "success", "data": {"result": res_data}}
                
                elif action == "list_contacts":
                     url = f"{base_url}/contacts"
                     async with session.get(url, headers=headers) as resp:
                         res_data = await resp.json()
                         return {"status": "success", "data": {"result": res_data.get("data", [])}}
                
                elif action == "send_message":
                    body = self.get_config("body")
                    if not body: return {"status": "error", "error": "body required"}
                    
                    # Usually admin initiated
                    user_id = "..." # Would need user config
                    # simplified example:
                    payload = {
                        "message_type": "inapp",
                        "body": body,
                        "from": {"type": "admin", "id": "admin_id"},
                        "to": {"type": "user", "email": email}
                    }
                    # ... implementation depends on exact requirements
                    pass 

            return {"status": "error", "error": f"Unsupported action: {action}"}

        except Exception as e:
            return {"status": "error", "error": f"Intercom Node Failed: {str(e)}"}
