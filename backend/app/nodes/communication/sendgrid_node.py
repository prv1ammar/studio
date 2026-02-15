"""
SendGrid Node - Studio Standard (Universal Method)
Batch 104: Communication Essentials
"""
from typing import Any, Dict, Optional
import aiohttp
from ...base import BaseNode
from ...registry import register_node

@register_node("sendgrid_node")
class SendGridNode(BaseNode):
    """
    SendGrid transactional email service integration.
    """
    node_type = "sendgrid_node"
    version = "1.0.0"
    category = "communication"
    credentials_required = ["sendgrid_auth"]

    inputs = {
        "action": {
            "type": "dropdown",
            "default": "send_email",
            "options": ["send_email", "send_template", "add_contact", "list_contacts", "create_list", "get_stats"],
            "description": "SendGrid action"
        },
        "to_email": {
            "type": "string",
            "optional": True
        },
        "from_email": {
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
        },
        "template_id": {
            "type": "string",
            "optional": True
        },
        "dynamic_data": {
            "type": "string",
            "optional": True,
            "description": "JSON for template variables"
        }
    }

    outputs = {
        "result": {"type": "any"},
        "status": {"type": "string"}
    }

    async def execute(self, input_data: Any, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        try:
            creds = await self.get_credential("sendgrid_auth")
            api_key = creds.get("api_key")
            
            if not api_key:
                return {"status": "error", "error": "SendGrid API key required"}

            base_url = "https://api.sendgrid.com/v3"
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            }
            
            action = self.get_config("action", "send_email")

            async with aiohttp.ClientSession() as session:
                if action == "send_email":
                    to_email = self.get_config("to_email")
                    from_email = self.get_config("from_email")
                    subject = self.get_config("subject")
                    content = self.get_config("content") or str(input_data)
                    
                    if not all([to_email, from_email, subject]):
                        return {"status": "error", "error": "to_email, from_email, and subject required"}
                    
                    url = f"{base_url}/mail/send"
                    payload = {
                        "personalizations": [
                            {
                                "to": [{"email": to_email}]
                            }
                        ],
                        "from": {"email": from_email},
                        "subject": subject,
                        "content": [
                            {
                                "type": "text/plain",
                                "value": content
                            }
                        ]
                    }
                    
                    async with session.post(url, headers=headers, json=payload) as resp:
                        if resp.status not in [200, 202]:
                            error_text = await resp.text()
                            return {"status": "error", "error": f"SendGrid API Error {resp.status}: {error_text}"}
                        return {"status": "success", "data": {"result": {"message": "Email sent successfully", "status_code": resp.status}}}

                elif action == "send_template":
                    to_email = self.get_config("to_email")
                    from_email = self.get_config("from_email")
                    template_id = self.get_config("template_id")
                    dynamic_data_str = self.get_config("dynamic_data", "{}")
                    
                    if not all([to_email, from_email, template_id]):
                        return {"status": "error", "error": "to_email, from_email, and template_id required"}
                    
                    import json
                    dynamic_data = json.loads(dynamic_data_str) if isinstance(dynamic_data_str, str) else dynamic_data_str
                    
                    url = f"{base_url}/mail/send"
                    payload = {
                        "personalizations": [
                            {
                                "to": [{"email": to_email}],
                                "dynamic_template_data": dynamic_data
                            }
                        ],
                        "from": {"email": from_email},
                        "template_id": template_id
                    }
                    
                    async with session.post(url, headers=headers, json=payload) as resp:
                        if resp.status not in [200, 202]:
                            error_text = await resp.text()
                            return {"status": "error", "error": f"SendGrid API Error {resp.status}: {error_text}"}
                        return {"status": "success", "data": {"result": {"message": "Template email sent", "status_code": resp.status}}}

                elif action == "add_contact":
                    email = self.get_config("to_email") or str(input_data)
                    
                    if not email:
                        return {"status": "error", "error": "email required"}
                    
                    url = f"{base_url}/marketing/contacts"
                    payload = {
                        "contacts": [
                            {"email": email}
                        ]
                    }
                    
                    async with session.put(url, headers=headers, json=payload) as resp:
                        if resp.status not in [200, 202]:
                            error_text = await resp.text()
                            return {"status": "error", "error": f"SendGrid API Error {resp.status}: {error_text}"}
                        res_data = await resp.json()
                        return {"status": "success", "data": {"result": res_data}}

                elif action == "list_contacts":
                    url = f"{base_url}/marketing/contacts"
                    async with session.get(url, headers=headers) as resp:
                        if resp.status != 200:
                            error_text = await resp.text()
                            return {"status": "error", "error": f"SendGrid API Error {resp.status}: {error_text}"}
                        res_data = await resp.json()
                        return {"status": "success", "data": {"result": res_data.get("result", [])}}

                elif action == "get_stats":
                    url = f"{base_url}/stats?start_date=2024-01-01"
                    async with session.get(url, headers=headers) as resp:
                        if resp.status != 200:
                            error_text = await resp.text()
                            return {"status": "error", "error": f"SendGrid API Error {resp.status}: {error_text}"}
                        res_data = await resp.json()
                        return {"status": "success", "data": {"result": res_data}}

                return {"status": "error", "error": f"Unsupported action: {action}"}

        except Exception as e:
            return {"status": "error", "error": f"SendGrid Node Failed: {str(e)}"}
