"""
Freshdesk Node - Studio Standard (Universal Method)
Batch 97: Support & Ticketing (Deepening Parity)
"""
from typing import Any, Dict, Optional, List
import aiohttp
import base64
from ...base import BaseNode
from ...registry import register_node

@register_node("freshdesk_node")
class FreshdeskNode(BaseNode):
    """
    Manage tickets and contacts via Freshdesk API v2.
    """
    node_type = "freshdesk_node"
    version = "1.0.0"
    category = "support"
    credentials_required = ["freshdesk_auth"]

    inputs = {
        "action": {
            "type": "dropdown",
            "default": "list_tickets",
            "options": ["list_tickets", "get_ticket", "create_ticket", "update_ticket", "delete_ticket"],
            "description": "Freshdesk action"
        },
        "ticket_id": {
            "type": "string",
            "optional": True
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
            "type": "dropdown",
            "default": "1",
            "options": ["1", "2", "3", "4"],
            "description": "1=Low, 2=Medium, 3=High, 4=Urgent"
        },
        "status": {
             "type": "dropdown",
             "default": "2",
             "options": ["2", "3", "4", "5"],
             "description": "2=Open, 3=Pending, 4=Resolved, 5=Closed"
        }
    }

    outputs = {
        "result": {"type": "any"},
        "status": {"type": "string"}
    }

    async def execute(self, input_data: Any, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        try:
            # 1. Authentication
            creds = await self.get_credential("freshdesk_auth")
            domain = creds.get("domain") # e.g. company.freshdesk.com
            api_key = creds.get("api_key")
            
            if not domain or not api_key:
                return {"status": "error", "error": "Freshdesk Domain (URL) and API Key required."}

            # Canonicalize domain
            if not domain.startswith("http"):
                base_url = f"https://{domain}/api/v2"
            else:
                base_url = f"{domain.rstrip('/')}/api/v2"

            # Basic Auth: api_key:X
            auth_str = f"{api_key}:X"
            b64_auth = base64.b64encode(auth_str.encode()).decode()
            
            headers = {
                "Authorization": f"Basic {b64_auth}",
                "Content-Type": "application/json"
            }
            
            action = self.get_config("action", "list_tickets")

            async with aiohttp.ClientSession() as session:
                if action == "list_tickets":
                    url = f"{base_url}/tickets"
                    async with session.get(url, headers=headers) as resp:
                        if resp.status != 200:
                            return {"status": "error", "error": f"Freshdesk API Error: {resp.status}"}
                        res_data = await resp.json()
                        return {"status": "success", "data": {"result": res_data}}

                elif action == "get_ticket":
                    ticket_id = self.get_config("ticket_id") or str(input_data)
                    url = f"{base_url}/tickets/{ticket_id}"
                    async with session.get(url, headers=headers) as resp:
                        if resp.status != 200:
                            return {"status": "error", "error": f"Freshdesk API Error: {resp.status}"}
                        res_data = await resp.json()
                        return {"status": "success", "data": {"result": res_data}}

                elif action == "create_ticket":
                    subject = self.get_config("subject")
                    description = self.get_config("description")
                    email = self.get_config("email")
                    priority = int(self.get_config("priority", "1"))
                    status = int(self.get_config("status", "2"))
                    
                    if not subject or not description or not email:
                        return {"status": "error", "error": "subject, description, and email required"}
                    
                    url = f"{base_url}/tickets"
                    payload = {
                        "subject": subject,
                        "description": description,
                        "email": email,
                        "priority": priority,
                        "status": status
                    }
                    async with session.post(url, headers=headers, json=payload) as resp:
                        if resp.status != 201:
                            text = await resp.text()
                            return {"status": "error", "error": f"Freshdesk API Error: {resp.status} - {text}"}
                        res_data = await resp.json()
                        return {"status": "success", "data": {"result": res_data}}

                elif action == "update_ticket":
                    ticket_id = self.get_config("ticket_id")
                    if not ticket_id: return {"status": "error", "error": "ticket_id required"}
                    
                    payload = {}
                    if self.get_config("subject"): payload["subject"] = self.get_config("subject")
                    if self.get_config("description"): payload["description"] = self.get_config("description")
                    if self.get_config("priority"): payload["priority"] = int(self.get_config("priority"))
                    if self.get_config("status"): payload["status"] = int(self.get_config("status"))
                    
                    url = f"{base_url}/tickets/{ticket_id}"
                    async with session.put(url, headers=headers, json=payload) as resp:
                        if resp.status != 200:
                            return {"status": "error", "error": f"Freshdesk API Error: {resp.status}"}
                        res_data = await resp.json()
                        return {"status": "success", "data": {"result": res_data}}

                elif action == "delete_ticket":
                    ticket_id = self.get_config("ticket_id")
                    if not ticket_id: return {"status": "error", "error": "ticket_id required"}
                    
                    url = f"{base_url}/tickets/{ticket_id}"
                    async with session.delete(url, headers=headers) as resp:
                        if resp.status != 204:
                            return {"status": "error", "error": f"Freshdesk API Error: {resp.status}"}
                        return {"status": "success", "data": {"result": {"message": "Ticket deleted"}}}

                return {"status": "error", "error": f"Unsupported action: {action}"}

        except Exception as e:
            return {"status": "error", "error": f"Freshdesk Node Failed: {str(e)}"}
