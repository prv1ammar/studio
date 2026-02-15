"""
Help Scout Node - Studio Standard (Universal Method)
Batch 109: Analytics & Support
"""
from typing import Any, Dict, Optional
import aiohttp
from ...base import BaseNode
from ...registry import register_node

@register_node("help_scout_node")
class HelpScoutNode(BaseNode):
    """
    Help Scout integration for customer service.
    """
    node_type = "help_scout_node"
    version = "1.0.0"
    category = "support"
    credentials_required = ["help_scout_auth"]

    inputs = {
        "action": {
            "type": "dropdown",
            "default": "create_conversation",
            "options": ["create_conversation", "list_conversations", "create_customer"],
            "description": "Help Scout action"
        },
        "mailbox_id": {
            "type": "string",
            "optional": True
        },
        "subject": {
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
            creds = await self.get_credential("help_scout_auth")
            access_token = creds.get("access_token")
            
            if not access_token:
                return {"status": "error", "error": "Help Scout access token required"}

            base_url = "https://api.helpscout.net/v2"
            headers = {"Authorization": f"Bearer {access_token}", "Content-Type": "application/json"}
            
            action = self.get_config("action", "create_conversation")

            async with aiohttp.ClientSession() as session:
                if action == "create_conversation":
                    mailbox_id = self.get_config("mailbox_id")
                    subject = self.get_config("subject")
                    # Needs more inputs like customer, threads ideally
                    
                    if not mailbox_id or not subject:
                        return {"status": "error", "error": "mailbox_id and subject required"}
                    
                    # Simplified payload for conversation
                    import json
                    payload = {
                        "subject": subject,
                        "mailboxId": int(mailbox_id),
                        "status": "active",
                        "type": "email",
                        "threads": [
                            {
                                "type": "customer",
                                "text": "New conversation via Studio", # Placeholder
                                "customer": {"email": "customer@example.com"} # Placeholder, input needed
                            }
                        ]
                    }
                    
                    url = f"{base_url}/conversations"
                    async with session.post(url, headers=headers, json=payload) as resp:
                         if resp.status != 201:
                            error_text = await resp.text()
                            return {"status": "error", "error": f"Help Scout API Error {resp.status}: {error_text}"}
                         # 201 Created returns Location header typically
                         res_loc = resp.headers.get("Location", "")
                         return {"status": "success", "data": {"result": {"location": res_loc}}}
                
                elif action == "list_conversations":
                     url = f"{base_url}/conversations"
                     if self.get_config("mailbox_id"):
                         url += f"?mailboxId={self.get_config('mailbox_id')}"
                         
                     async with session.get(url, headers=headers) as resp:
                         res_data = await resp.json()
                         return {"status": "success", "data": {"result": res_data.get("_embedded", {}).get("conversations", [])}}

            return {"status": "error", "error": f"Unsupported action: {action}"}

        except Exception as e:
            return {"status": "error", "error": f"Help Scout Node Failed: {str(e)}"}
