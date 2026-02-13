"""
Brevo (Sendinblue) Node - Studio Standard
Batch 62: Marketing Automation
"""
from typing import Any, Dict, Optional, List
import aiohttp
from ...base import BaseNode
from ...registry import register_node

@register_node("brevo_node")
class BrevoNode(BaseNode):
    """
    Multi-channel marketing automation (Email, SMS) via Brevo.
    Supports contact management and transactional emails.
    """
    node_type = "brevo_node"
    version = "1.0.0"
    category = "marketing"
    credentials_required = ["brevo_auth"]

    inputs = {
        "action": {
            "type": "dropdown",
            "default": "get_contacts",
            "options": ["get_contacts", "create_contact", "send_transactional_email", "get_account"],
            "description": "Brevo action"
        },
        "email": {
            "type": "string",
            "optional": True,
            "description": "Contact email"
        },
        "subject": {
            "type": "string",
            "optional": True,
            "description": "Email subject"
        },
        "content": {
            "type": "string",
            "optional": True,
            "description": "HTML or Text content"
        },
        "list_ids": {
            "type": "array",
            "optional": True,
            "description": "List IDs to add contact to"
        }
    }

    outputs = {
        "result": {"type": "any"},
        "status": {"type": "string"},
        "count": {"type": "number"}
    }

    async def execute(self, input_data: Any, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        try:
            # 1. Resolve Auth
            creds = await self.get_credential("brevo_auth")
            api_key = creds.get("api_key") if creds else self.get_config("api_key")
            
            if not api_key:
                return {"status": "error", "error": "Brevo API Key is required."}

            headers = {
                "api-key": api_key,
                "Accept": "application/json",
                "Content-Type": "application/json"
            }
            
            base_url = "https://api.brevo.com/v3"
            action = self.get_config("action", "get_contacts")

            async with aiohttp.ClientSession() as session:
                if action == "get_contacts":
                    url = f"{base_url}/contacts"
                    async with session.get(url, headers=headers) as resp:
                        res_data = await resp.json()
                        return {"status": "success", "data": {"result": res_data.get("contacts", []), "count": res_data.get("count", 0)}}

                elif action == "create_contact":
                    url = f"{base_url}/contacts"
                    email = self.get_config("email") or str(input_data)
                    list_ids = self.get_config("list_ids", [])
                    payload = {"email": email, "listIds": list_ids}
                    async with session.post(url, headers=headers, json=payload) as resp:
                        res_data = await resp.json()
                        return {"status": "success", "data": {"result": res_data, "status": "created"}}

                elif action == "send_transactional_email":
                    url = f"{base_url}/smtp/email"
                    email = self.get_config("email")
                    subject = self.get_config("subject")
                    content = self.get_config("content") or str(input_data)
                    
                    payload = {
                        "to": [{"email": email}],
                        "subject": subject,
                        "htmlContent": content,
                        "sender": {"name": "Studio Agent", "email": "agent@studio.ai"} # Placeholder
                    }
                    async with session.post(url, headers=headers, json=payload) as resp:
                        res_data = await resp.json()
                        return {"status": "success", "data": {"result": res_data, "status": "sent"}}

                return {"status": "error", "error": f"Unsupported Brevo action: {action}"}

        except Exception as e:
            return {"status": "error", "error": f"Brevo Node Failed: {str(e)}"}
