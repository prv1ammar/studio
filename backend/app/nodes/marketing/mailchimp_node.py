"""
Mailchimp Node - Studio Standard (Universal Method)
Batch 108: Marketing & CRM
"""
from typing import Any, Dict, Optional
import aiohttp
from ...base import BaseNode
from ...registry import register_node

@register_node("mailchimp_node")
class MailchimpNode(BaseNode):
    """
    Mailchimp integration for email marketing campaigns.
    """
    node_type = "mailchimp_node"
    version = "1.0.0"
    category = "marketing"
    credentials_required = ["mailchimp_auth"]

    inputs = {
        "action": {
            "type": "dropdown",
            "default": "add_subscriber",
            "options": ["add_subscriber", "list_audiences", "create_campaign"],
            "description": "Mailchimp action"
        },
        "list_id": {
            "type": "string",
            "optional": True
        },
        "email_address": {
            "type": "string",
            "optional": True
        },
        "status": {
            "type": "dropdown",
            "default": "subscribed",
            "options": ["subscribed", "unsubscribed", "cleaned", "pending"],
            "description": "Subscriber status"
        }
    }

    outputs = {
        "result": {"type": "any"},
        "status": {"type": "string"}
    }

    async def execute(self, input_data: Any, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        try:
            creds = await self.get_credential("mailchimp_auth")
            api_key = creds.get("api_key")
            server_prefix = creds.get("server_prefix") # e.g. us19
            
            if not api_key or not server_prefix:
                return {"status": "error", "error": "Mailchimp API key and server prefix required"}

            base_url = f"https://{server_prefix}.api.mailchimp.com/3.0"
            headers = {"Authorization": f"Bearer {api_key}"}
            
            action = self.get_config("action", "add_subscriber")

            async with aiohttp.ClientSession() as session:
                if action == "add_subscriber":
                    list_id = self.get_config("list_id")
                    email = self.get_config("email_address")
                    status = self.get_config("status", "subscribed")
                    
                    if not list_id or not email:
                         return {"status": "error", "error": "list_id and email_address required"}
                         
                    payload = {
                        "email_address": email,
                        "status": status
                    }
                    
                    url = f"{base_url}/lists/{list_id}/members"
                    async with session.post(url, headers=headers, json=payload, auth=aiohttp.BasicAuth("anystring", api_key)) as resp:
                         # Mailchimp uses Basic Auth with any username and API key as password
                         if resp.status not in [200, 201]: # 204? maybe not for add
                            error_text = await resp.text()
                            return {"status": "error", "error": f"Mailchimp API Error {resp.status}: {error_text}"}
                         res_data = await resp.json()
                         return {"status": "success", "data": {"result": res_data}}
                
                elif action == "list_audiences":
                    url = f"{base_url}/lists"
                    async with session.get(url, headers=headers, auth=aiohttp.BasicAuth("anystring", api_key)) as resp:
                         res_data = await resp.json()
                         return {"status": "success", "data": {"result": res_data.get("lists", [])}}

            return {"status": "error", "error": f"Unsupported action: {action}"}

        except Exception as e:
            return {"status": "error", "error": f"Mailchimp Node Failed: {str(e)}"}
