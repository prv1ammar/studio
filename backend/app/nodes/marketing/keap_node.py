"""
Keap Node - Studio Standard (Universal Method)
Batch 108: Marketing & CRM
"""
from typing import Any, Dict, Optional
import aiohttp
from ..base import BaseNode
from ..registry import register_node

@register_node("keap_node")
class KeapNode(BaseNode):
    """
    Keap (Infusionsoft) CRM and Marketing Automation.
    """
    node_type = "keap_node"
    version = "1.0.0"
    category = "marketing"
    credentials_required = ["keap_auth"]


    properties = [
        {
            'displayName': 'Operation',
            'name': 'operation',
            'type': 'options',
            'default': 'create_contact',
            'options': [
                {'name': 'Create Contact', 'value': 'create_contact'},
                {'name': 'List Contacts', 'value': 'list_contacts'},
                {'name': 'Add Tag', 'value': 'add_tag'},
                {'name': 'Create Company', 'value': 'create_company'},
            ],
            'description': 'Keap action',
        },
        {
            'displayName': 'Email',
            'name': 'email',
            'type': 'string',
            'default': '',
        },
        {
            'displayName': 'Family Name',
            'name': 'family_name',
            'type': 'string',
            'default': '',
        },
        {
            'displayName': 'Given Name',
            'name': 'given_name',
            'type': 'string',
            'default': '',
        },
    ]
    inputs = {
        "action": {
            "type": "dropdown",
            "default": "create_contact",
            "options": ["create_contact", "list_contacts", "add_tag", "create_company"],
            "description": "Keap action"
        },
        "email": {
            "type": "string",
            "optional": True
        },
        "given_name": {
            "type": "string",
            "optional": True
        },
        "family_name": {
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
            creds = await self.get_credential("keap_auth")
            access_token = creds.get("access_token")
            
            if not access_token:
                return {"status": "error", "error": "Keap access token required"}

            base_url = "https://api.infusionsoft.com/crm/rest/v1"
            headers = {"Authorization": f"Bearer {access_token}"}
            
            action = self.get_config("action", "create_contact")

            async with aiohttp.ClientSession() as session:
                if action == "create_contact":
                    email = self.get_config("email")
                    given_name = self.get_config("given_name")
                    family_name = self.get_config("family_name")
                    
                    if not email:
                         # Email often required for uniqueness
                         pass
                    
                    payload = {"email_addresses": [{"email": email, "field": "EMAIL1"}]}
                    if given_name: payload["given_name"] = given_name
                    if family_name: payload["family_name"] = family_name
                    
                    url = f"{base_url}/contacts"
                    async with session.post(url, headers=headers, json=payload) as resp:
                         if resp.status != 201:
                            error_text = await resp.text()
                            return {"status": "error", "error": f"Keap API Error {resp.status}: {error_text}"}
                         res_data = await resp.json()
                         return {"status": "success", "data": {"result": res_data}}
                
                elif action == "list_contacts":
                     url = f"{base_url}/contacts"
                     async with session.get(url, headers=headers) as resp:
                         res_data = await resp.json()
                         return {"status": "success", "data": {"result": res_data.get("contacts", [])}}

            return {"status": "error", "error": f"Unsupported action: {action}"}

        except Exception as e:
            return {"status": "error", "error": f"Keap Node Failed: {str(e)}"}