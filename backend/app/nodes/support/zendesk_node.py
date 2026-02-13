"""
Zendesk Node - Studio Standard (Universal Method)
Batch 97: Support & Ticketing (Deepening Parity)
"""
from typing import Any, Dict, Optional, List
import aiohttp
import base64
from ...base import BaseNode
from ...registry import register_node

@register_node("zendesk_node")
class ZendeskNode(BaseNode):
    """
    Manage tickets and users via Zendesk Support API.
    """
    node_type = "zendesk_node"
    version = "1.0.0"
    category = "support"
    credentials_required = ["zendesk_auth"]

    inputs = {
        "action": {
            "type": "dropdown",
            "default": "list_tickets",
            "options": ["list_tickets", "get_ticket", "create_ticket", "update_ticket", "search_users"],
            "description": "Zendesk action"
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
        "priority": {
            "type": "dropdown",
            "default": "normal",
            "options": ["urgent", "high", "normal", "low"],
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
            creds = await self.get_credential("zendesk_auth")
            subdomain = creds.get("subdomain")
            email = creds.get("email")
            api_token = creds.get("api_token")
            
            if not subdomain or not email or not api_token:
                return {"status": "error", "error": "Zendesk Subdomain, Email and API Token required."}

            # Zendesk Basic Auth: email/token:api_token
            auth_str = f"{email}/token:{api_token}"
            b64_auth = base64.b64encode(auth_str.encode()).decode()
            
            headers = {
                "Authorization": f"Basic {b64_auth}",
                "Content-Type": "application/json"
            }
            
            # 2. Connect to Real API
            base_url = f"https://{subdomain}.zendesk.com/api/v2"
            action = self.get_config("action", "list_tickets")

            async with aiohttp.ClientSession() as session:
                if action == "list_tickets":
                    url = f"{base_url}/tickets.json"
                    async with session.get(url, headers=headers) as resp:
                        if resp.status != 200:
                            return {"status": "error", "error": f"Zendesk API Error: {resp.status}"}
                        res_data = await resp.json()
                        return {"status": "success", "data": {"result": res_data.get("tickets", [])}}

                elif action == "get_ticket":
                    ticket_id = self.get_config("ticket_id") or str(input_data)
                    url = f"{base_url}/tickets/{ticket_id}.json"
                    async with session.get(url, headers=headers) as resp:
                        if resp.status != 200:
                            return {"status": "error", "error": f"Zendesk API Error: {resp.status}"}
                        res_data = await resp.json()
                        return {"status": "success", "data": {"result": res_data.get("ticket", {})}}

                elif action == "create_ticket":
                    subject = self.get_config("subject")
                    description = self.get_config("description")
                    priority = self.get_config("priority", "normal")
                    
                    if not subject or not description:
                        return {"status": "error", "error": "subject and description required"}
                    
                    url = f"{base_url}/tickets.json"
                    payload = {
                        "ticket": {
                            "subject": subject,
                            "comment": {"body": description},
                            "priority": priority
                        }
                    }
                    async with session.post(url, headers=headers, json=payload) as resp:
                        if resp.status != 201:
                            return {"status": "error", "error": f"Zendesk API Error: {resp.status}"}
                        res_data = await resp.json()
                        return {"status": "success", "data": {"result": res_data.get("ticket", {})}}

                elif action == "update_ticket":
                    ticket_id = self.get_config("ticket_id")
                    if not ticket_id:
                        return {"status": "error", "error": "ticket_id required"}

                    # Optional updates
                    payload = {"ticket": {}}
                    if self.get_config("subject"):
                        payload["ticket"]["subject"] = self.get_config("subject")
                    if self.get_config("priority"):
                        payload["ticket"]["priority"] = self.get_config("priority")
                    
                    url = f"{base_url}/tickets/{ticket_id}.json"
                    async with session.put(url, headers=headers, json=payload) as resp:
                         if resp.status != 200:
                            return {"status": "error", "error": f"Zendesk API Error: {resp.status}"}
                         res_data = await resp.json()
                         return {"status": "success", "data": {"result": res_data.get("ticket", {})}}

                elif action == "search_users":
                    query = self.get_config("subject") or str(input_data) # Reusing subject field for query
                    url = f"{base_url}/users/search.json"
                    params = {"query": query}
                    async with session.get(url, headers=headers, params=params) as resp:
                        if resp.status != 200:
                            return {"status": "error", "error": f"Zendesk API Error: {resp.status}"}
                        res_data = await resp.json()
                        return {"status": "success", "data": {"result": res_data.get("users", [])}}

                return {"status": "error", "error": f"Unsupported action: {action}"}

        except Exception as e:
            return {"status": "error", "error": f"Zendesk Node Failed: {str(e)}"}
