"""
HubSpot Service Node - Studio Standard (Universal Method)
Batch 97: Support & Ticketing (Deepening Parity)
"""
from typing import Any, Dict, Optional, List
import aiohttp
from ..base import BaseNode
from ..registry import register_node

@register_node("hubspot_service_node")
class HubSpotServiceNode(BaseNode):
    """
    Manage HubSpot Tickets and Service objects.
    """
    node_type = "hubspot_service_node"
    version = "1.0.0"
    category = "support"
    credentials_required = ["hubspot_auth"]


    properties = [
        {
            'displayName': 'Operation',
            'name': 'operation',
            'type': 'options',
            'default': 'list_tickets',
            'options': [
                {'name': 'List Tickets', 'value': 'list_tickets'},
                {'name': 'Get Ticket', 'value': 'get_ticket'},
                {'name': 'Create Ticket', 'value': 'create_ticket'},
                {'name': 'Update Ticket', 'value': 'update_ticket'},
            ],
            'description': 'HubSpot Service action',
        },
        {
            'displayName': 'Content',
            'name': 'content',
            'type': 'string',
            'default': '',
        },
        {
            'displayName': 'Pipeline',
            'name': 'pipeline',
            'type': 'string',
            'default': '0',
            'description': 'Pipeline ID',
        },
        {
            'displayName': 'Stage',
            'name': 'stage',
            'type': 'string',
            'default': '1',
            'description': 'Stage ID',
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
            "default": "list_tickets",
            "options": ["list_tickets", "get_ticket", "create_ticket", "update_ticket"],
            "description": "HubSpot Service action"
        },
        "ticket_id": {
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
        "pipeline": {
            "type": "string",
            "default": "0",
            "description": "Pipeline ID"
        },
        "stage": {
            "type": "string",
            "default": "1",
            "description": "Stage ID"
        }
    }

    outputs = {
        "result": {"type": "any"},
        "status": {"type": "string"}
    }

    async def execute(self, input_data: Any, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        try:
            # 1. Authentication
            creds = await self.get_credential("hubspot_auth")
            access_token = creds.get("access_token")
            
            if not access_token:
                return {"status": "error", "error": "HubSpot Access Token required."}

            headers = {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json"
            }
            
            # 2. Connect to Real API
            base_url = "https://api.hubapi.com/crm/v3/objects/tickets"
            action = self.get_config("action", "list_tickets")

            async with aiohttp.ClientSession() as session:
                if action == "list_tickets":
                    async with session.get(base_url, headers=headers) as resp:
                        if resp.status != 200:
                            return {"status": "error", "error": f"HubSpot API Error: {resp.status}"}
                        res_data = await resp.json()
                        return {"status": "success", "data": {"result": res_data.get("results", [])}}

                elif action == "get_ticket":
                    ticket_id = self.get_config("ticket_id") or str(input_data)
                    url = f"{base_url}/{ticket_id}"
                    async with session.get(url, headers=headers) as resp:
                        if resp.status != 200:
                            return {"status": "error", "error": f"HubSpot API Error: {resp.status}"}
                        res_data = await resp.json()
                        return {"status": "success", "data": {"result": res_data}}

                elif action == "create_ticket":
                    subject = self.get_config("subject")
                    content = self.get_config("content")
                    pipeline = self.get_config("pipeline", "0")
                    stage = self.get_config("stage", "1")
                    
                    if not subject:
                        return {"status": "error", "error": "subject required"}
                    
                    payload = {
                        "properties": {
                            "subject": subject,
                            "content": content,
                            "hs_pipeline": pipeline,
                            "hs_pipeline_stage": stage,
                            "hs_ticket_priority": "LOW" # Defaulting for now
                        }
                    }
                    async with session.post(base_url, headers=headers, json=payload) as resp:
                        if resp.status != 201:
                            text = await resp.text()
                            return {"status": "error", "error": f"HubSpot API Error: {resp.status} - {text}"}
                        res_data = await resp.json()
                        return {"status": "success", "data": {"result": res_data}}

                elif action == "update_ticket":
                    ticket_id = self.get_config("ticket_id")
                    if not ticket_id: return {"status": "error", "error": "ticket_id required"}
                    
                    props = {}
                    if self.get_config("subject"): props["subject"] = self.get_config("subject")
                    if self.get_config("content"): props["content"] = self.get_config("content")
                    if self.get_config("stage"): props["hs_pipeline_stage"] = self.get_config("stage")
                    
                    url = f"{base_url}/{ticket_id}"
                    payload = {"properties": props}
                    
                    async with session.patch(url, headers=headers, json=payload) as resp:
                        if resp.status != 200:
                             return {"status": "error", "error": f"HubSpot API Error: {resp.status}"}
                        res_data = await resp.json()
                        return {"status": "success", "data": {"result": res_data}}

                return {"status": "error", "error": f"Unsupported action: {action}"}

        except Exception as e:
            return {"status": "error", "error": f"HubSpot Service Node Failed: {str(e)}"}