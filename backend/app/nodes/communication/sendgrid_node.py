"""
SendGrid Node - Studio Standard (Universal Method)
Batch 90: CRM & Marketing (n8n Critical)
"""
from typing import Any, Dict, Optional, List
import aiohttp
from ...base import BaseNode
from ...registry import register_node

@register_node("sendgrid_node")
class SendGridNode(BaseNode):
    """
    Send emails and manage contacts via SendGrid API.
    """
    node_type = "sendgrid_node"
    version = "1.0.0"
    category = "communication"
    credentials_required = ["sendgrid_auth"]

    inputs = {
        "action": {
            "type": "dropdown",
            "default": "send_email",
            "options": ["send_email", "add_contact", "list_contacts", "get_stats"],
            "description": "SendGrid action"
        },
        "to_email": {
            "type": "string",
            "optional": True
        },
        "subject": {
            "type": "string",
            "optional": True
        },
        "content": {
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
            # 1. Authentication
            creds = await self.get_credential("sendgrid_auth")
            api_key = creds.get("api_key")
            
            if not api_key:
                return {"status": "error", "error": "SendGrid API Key required."}

            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            }
            
            # 2. Connect to Real API
            base_url = "https://api.sendgrid.com/v3"
            action = self.get_config("action", "send_email")

            async with aiohttp.ClientSession() as session:
                if action == "send_email":
                    to_email = self.get_config("to_email")
                    subject = self.get_config("subject", "Studio Workflow Email")
                    content = self.get_config("content") or str(input_data)
                    from_email = creds.get("from_email", "noreply@studio.com")
                    
                    if not to_email:
                        return {"status": "error", "error": "to_email required"}
                    
                    url = f"{base_url}/mail/send"
                    payload = {
                        "personalizations": [{
                            "to": [{"email": to_email}]
                        }],
                        "from": {"email": from_email},
                        "subject": subject,
                        "content": [{
                            "type": "text/plain",
                            "value": content
                        }]
                    }
                    async with session.post(url, headers=headers, json=payload) as resp:
                        if resp.status not in [200, 202]:
                            return {"status": "error", "error": f"SendGrid Error: {resp.status} - {await resp.text()}"}
                        return {"status": "success", "data": {"result": {"message": "Email sent successfully"}}}

                elif action == "add_contact":
                    email = self.get_config("to_email") or str(input_data)
                    url = f"{base_url}/marketing/contacts"
                    payload = {
                        "contacts": [{"email": email}]
                    }
                    async with session.put(url, headers=headers, json=payload) as resp:
                        if resp.status not in [200, 202]:
                            return {"status": "error", "error": f"SendGrid Error: {resp.status}"}
                        res_data = await resp.json()
                        return {"status": "success", "data": {"result": res_data}}

                elif action == "list_contacts":
                    url = f"{base_url}/marketing/contacts"
                    async with session.get(url, headers=headers) as resp:
                        if resp.status != 200:
                            return {"status": "error", "error": f"SendGrid Error: {resp.status}"}
                        res_data = await resp.json()
                        return {"status": "success", "data": {"result": res_data.get("result", [])}}

                return {"status": "error", "error": f"Unsupported action: {action}"}

        except Exception as e:
            return {"status": "error", "error": f"SendGrid Node Failed: {str(e)}"}
