"""
Zendesk Node - Studio Standard (Universal Method)
Batch 109: Analytics & Support
"""
from typing import Any, Dict, Optional
import aiohttp
from ..base import BaseNode
from ..registry import register_node

@register_node("zendesk_node")
class ZendeskNode(BaseNode):
    """
    Zendesk integration for customer support tickets.
    """
    node_type = "zendesk_node"
    version = "1.0.0"
    category = "support"
    credentials_required = ["zendesk_auth"]


    properties = [
        {
            'displayName': 'Operation',
            'name': 'operation',
            'type': 'options',
            'default': 'create_ticket',
            'options': [
                {'name': 'Create Ticket', 'value': 'create_ticket'},
                {'name': 'Get Ticket', 'value': 'get_ticket'},
                {'name': 'Update Ticket', 'value': 'update_ticket'},
                {'name': 'List Tickets', 'value': 'list_tickets'},
            ],
            'description': 'Zendesk action',
        },
        {
            'displayName': 'Description',
            'name': 'description',
            'type': 'string',
            'default': '',
        },
        {
            'displayName': 'Subject',
            'name': 'subject',
            'type': 'string',
            'default': '',
        },
        {
            'displayName': 'Ticket Id',
            'name': 'ticket_id',
            'type': 'string',
            'default': '',
        },
    ]
    inputs = {
        "action": {
            "type": "dropdown",
            "default": "create_ticket",
            "options": ["create_ticket", "get_ticket", "update_ticket", "list_tickets"],
            "description": "Zendesk action"
        },
        "subject": {
            "type": "string",
            "optional": True
        },
        "description": {
            "type": "string",
            "optional": True
        },
        "ticket_id": {
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
            creds = await self.get_credential("zendesk_auth")
            subdomain = creds.get("subdomain")
            email = creds.get("email")
            api_token = creds.get("api_token")
            # Or OAuth token
            
            if not subdomain or not email or not api_token:
                return {"status": "error", "error": "Zendesk subdomain, email, and API token required"}

            base_url = f"https://{subdomain}.zendesk.com/api/v2"
            auth = aiohttp.BasicAuth(f"{email}/token", api_token)
            headers = {"Content-Type": "application/json"}
            
            action = self.get_config("action", "create_ticket")

            async with aiohttp.ClientSession() as session:
                if action == "create_ticket":
                    subject = self.get_config("subject")
                    description = self.get_config("description") # Often comment.body
                    
                    if not subject or not description:
                        return {"status": "error", "error": "subject and description required"}
                        
                    payload = {
                        "ticket": {
                            "subject": subject,
                            "comment": {
                                "body": description
                            }
                        }
                    }
                    
                    url = f"{base_url}/tickets.json"
                    async with session.post(url, headers=headers, auth=auth, json=payload) as resp:
                         if resp.status != 201:
                            error_text = await resp.text()
                            return {"status": "error", "error": f"Zendesk API Error {resp.status}: {error_text}"}
                         res_data = await resp.json()
                         return {"status": "success", "data": {"result": res_data.get("ticket")}}
                
                elif action == "get_ticket":
                    ticket_id = self.get_config("ticket_id")
                    if not ticket_id: return {"status": "error", "error": "ticket_id required"}
                    
                    url = f"{base_url}/tickets/{ticket_id}.json"
                    async with session.get(url, headers=headers, auth=auth) as resp:
                         res_data = await resp.json()
                         return {"status": "success", "data": {"result": res_data.get("ticket")}}
                
                elif action == "list_tickets":
                     url = f"{base_url}/tickets.json"
                     async with session.get(url, headers=headers, auth=auth) as resp:
                         res_data = await resp.json()
                         return {"status": "success", "data": {"result": res_data.get("tickets", [])}}

            return {"status": "error", "error": f"Unsupported action: {action}"}

        except Exception as e:
            return {"status": "error", "error": f"Zendesk Node Failed: {str(e)}"}