"""
ActiveCampaign Node - Studio Standard (Universal Method)
Batch 108: Marketing & CRM
"""
from typing import Any, Dict, Optional
import aiohttp
from ..base import BaseNode
from ..registry import register_node

@register_node("activecampaign_node")
class ActiveCampaignNode(BaseNode):
    """
    ActiveCampaign integration for email marketing and CRM.
    """
    node_type = "activecampaign_node"
    version = "1.0.0"
    category = "marketing"
    credentials_required = ["activecampaign_auth"]


    properties = [
        {
            'displayName': 'Operation',
            'name': 'operation',
            'type': 'options',
            'default': 'create_contact',
            'options': [
                {'name': 'Create Contact', 'value': 'create_contact'},
                {'name': 'List Contacts', 'value': 'list_contacts'},
                {'name': 'Create Deal', 'value': 'create_deal'},
            ],
            'description': 'ActiveCampaign action',
        },
        {
            'displayName': 'Email',
            'name': 'email',
            'type': 'string',
            'default': '',
        },
        {
            'displayName': 'First Name',
            'name': 'first_name',
            'type': 'string',
            'default': '',
        },
    ]
    inputs = {
        "action": {
            "type": "dropdown",
            "default": "create_contact",
            "options": ["create_contact", "list_contacts", "create_deal"],
            "description": "ActiveCampaign action"
        },
        "email": {
            "type": "string",
            "optional": True
        },
        "first_name": {
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
            creds = await self.get_credential("activecampaign_auth")
            api_key = creds.get("api_key")
            api_url = creds.get("api_url")
            
            if not api_key or not api_url:
                return {"status": "error", "error": "ActiveCampaign API key and URL required"}

            base_url = f"{api_url}/api/3"
            headers = {"Api-Token": api_key}
            
            action = self.get_config("action", "create_contact")

            async with aiohttp.ClientSession() as session:
                if action == "create_contact":
                    email = self.get_config("email")
                    first_name = self.get_config("first_name")
                    
                    if not email:
                         return {"status": "error", "error": "email required"}
                         
                    payload = {"contact": {"email": email}}
                    if first_name:
                        payload["contact"]["firstName"] = first_name
                        
                    url = f"{base_url}/contacts"
                    async with session.post(url, headers=headers, json=payload) as resp:
                         if resp.status != 201:
                            error_text = await resp.text()
                            return {"status": "error", "error": f"ActiveCampaign API Error {resp.status}: {error_text}"}
                         res_data = await resp.json()
                         return {"status": "success", "data": {"result": res_data}}
                
                elif action == "list_contacts":
                    url = f"{base_url}/contacts"
                    async with session.get(url, headers=headers) as resp:
                         res_data = await resp.json()
                         return {"status": "success", "data": {"result": res_data.get("contacts", [])}}

            return {"status": "error", "error": f"Unsupported action: {action}"}

        except Exception as e:
            return {"status": "error", "error": f"ActiveCampaign Node Failed: {str(e)}"}