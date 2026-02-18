"""
Freshdesk Node - Studio Standard (Universal Method)
Batch 109: Analytics & Support
"""
from typing import Any, Dict, Optional
import aiohttp
from ..base import BaseNode
from ..registry import register_node

@register_node("freshdesk_node")
class FreshdeskNode(BaseNode):
    """
    Freshdesk integration for customer support.
    """
    node_type = "freshdesk_node"
    version = "1.0.0"
    category = "support"
    credentials_required = ["freshdesk_auth"]


    properties = [
        {
            'displayName': 'Operation',
            'name': 'operation',
            'type': 'options',
            'default': 'create_ticket',
            'options': [
                {'name': 'Create Ticket', 'value': 'create_ticket'},
                {'name': 'List Tickets', 'value': 'list_tickets'},
                {'name': 'Get Ticket', 'value': 'get_ticket'},
                {'name': 'Update Ticket', 'value': 'update_ticket'},
            ],
            'description': 'Freshdesk action',
        },
        {
            'displayName': 'Description',
            'name': 'description',
            'type': 'string',
            'default': '',
        },
        {
            'displayName': 'Email',
            'name': 'email',
            'type': 'string',
            'default': '',
        },
        {
            'displayName': 'Priority',
            'name': 'priority',
            'type': 'string',
            'default': 1,
            'description': '1 (low) - 4 (urgent)',
        },
        {
            'displayName': 'Status',
            'name': 'status',
            'type': 'string',
            'default': 2,
            'description': '2 (open), 3 (pending), etc.',
        },
        {
            'displayName': 'Subject',
            'name': 'subject',
            'type': 'string',
            'default': '',
        },
    ]
    inputs = {
        "action": {
            "type": "dropdown",
            "default": "create_ticket",
            "options": ["create_ticket", "list_tickets", "get_ticket", "update_ticket"],
            "description": "Freshdesk action"
        },
        "subject": {
            "type": "string",
            "optional": True
        },
        "description": {
            "type": "string",
            "optional": True
        },
        "email": {
            "type": "string",
            "optional": True
        },
        "priority": {
            "type": "number",
            "default": 1,
            "description": "1 (low) - 4 (urgent)"
        },
        "status": {
            "type": "number",
            "default": 2,
            "description": "2 (open), 3 (pending), etc."
        }
    }

    outputs = {
        "result": {"type": "any"},
        "status": {"type": "string"}
    }

    async def execute(self, input_data: Any, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        try:
            creds = await self.get_credential("freshdesk_auth")
            api_key = creds.get("api_key")
            domain = creds.get("domain")
            
            if not api_key or not domain:
                return {"status": "error", "error": "Freshdesk API key and domain required"}

            base_url = f"https://{domain}/api/v2"
            auth = aiohttp.BasicAuth(api_key, "X") # password dummy X
            headers = {"Content-Type": "application/json"}
            
            action = self.get_config("action", "create_ticket")

            async with aiohttp.ClientSession() as session:
                if action == "create_ticket":
                    subject = self.get_config("subject")
                    description = self.get_config("description")
                    email = self.get_config("email")
                    priority = int(self.get_config("priority", 1))
                    status = int(self.get_config("status", 2))
                    
                    if not subject or not description or not email:
                        return {"status": "error", "error": "subject, description, and email required"}
                        
                    payload = {
                        "subject": subject,
                        "description": description,
                        "email": email,
                        "priority": priority,
                        "status": status
                    }
                    
                    url = f"{base_url}/tickets"
                    async with session.post(url, headers=headers, auth=auth, json=payload) as resp:
                         if resp.status != 201:
                            error_text = await resp.text()
                            return {"status": "error", "error": f"Freshdesk API Error {resp.status}: {error_text}"}
                         res_data = await resp.json()
                         return {"status": "success", "data": {"result": res_data}}
                
                elif action == "list_tickets":
                     url = f"{base_url}/tickets"
                     async with session.get(url, headers=headers, auth=auth) as resp:
                         res_data = await resp.json()
                         return {"status": "success", "data": {"result": res_data}}
                
                elif action == "get_ticket":
                    ticket_id = self.get_config("ticket_id")
                    if not ticket_id: return {"status": "error", "error": "ticket_id required"}
                    
                    url = f"{base_url}/tickets/{ticket_id}"
                    async with session.get(url, headers=headers, auth=auth) as resp:
                         res_data = await resp.json()
                         return {"status": "success", "data": {"result": res_data}}

            return {"status": "error", "error": f"Unsupported action: {action}"}

        except Exception as e:
            return {"status": "error", "error": f"Freshdesk Node Failed: {str(e)}"}