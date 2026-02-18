"""
HubSpot Node - Studio Standard (Universal Method)
Batch 108: Marketing & CRM
"""
from typing import Any, Dict, Optional
import aiohttp
from ..base import BaseNode
from ..registry import register_node

@register_node("hubspot_node")
class HubSpotNode(BaseNode):
    """
    HubSpot CRM integration for marketing and sales.
    """
    node_type = "hubspot_node"
    version = "1.0.0"
    category = "marketing"
    credentials_required = ["hubspot_auth"]


    properties = [
        {
            'displayName': 'Operation',
            'name': 'operation',
            'type': 'options',
            'default': 'create_contact',
            'options': [
                {'name': 'Create Contact', 'value': 'create_contact'},
                {'name': 'List Contacts', 'value': 'list_contacts'},
                {'name': 'Update Contact', 'value': 'update_contact'},
                {'name': 'Search', 'value': 'search'},
            ],
            'description': 'HubSpot action',
        },
        {
            'displayName': 'Email',
            'name': 'email',
            'type': 'string',
            'default': '',
        },
        {
            'displayName': 'Firstname',
            'name': 'firstname',
            'type': 'string',
            'default': '',
        },
        {
            'displayName': 'Lastname',
            'name': 'lastname',
            'type': 'string',
            'default': '',
        },
        {
            'displayName': 'Properties',
            'name': 'properties',
            'type': 'string',
            'default': '',
            'description': 'JSON object of properties',
        },
    ]
    inputs = {
        "action": {
            "type": "dropdown",
            "default": "create_contact",
            "options": ["create_contact", "list_contacts", "update_contact", "search"],
            "description": "HubSpot action"
        },
        "email": {
            "type": "string",
            "optional": True
        },
        "firstname": {
            "type": "string",
            "optional": True
        },
        "lastname": {
            "type": "string",
            "optional": True
        },
        "properties": {
            "type": "string",
            "optional": True,
            "description": "JSON object of properties"
        }
    }

    outputs = {
        "result": {"type": "any"},
        "status": {"type": "string"}
    }

    async def execute(self, input_data: Any, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        try:
            creds = await self.get_credential("hubspot_auth")
            access_token = creds.get("access_token")
            
            if not access_token:
                return {"status": "error", "error": "HubSpot access token required"}

            base_url = "https://api.hubapi.com/crm/v3/objects"
            headers = {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json"
            }
            
            action = self.get_config("action", "create_contact")

            async with aiohttp.ClientSession() as session:
                if action == "create_contact":
                    email = self.get_config("email")
                    firstname = self.get_config("firstname")
                    lastname = self.get_config("lastname")
                    
                    if not email:
                         # Email is usually primary for HubSpot contacts
                         pass
                    
                    properties = {"email": email}
                    if firstname: properties["firstname"] = firstname
                    if lastname: properties["lastname"] = lastname
                    
                    # Merge extra properties if provided
                    extra_props = self.get_config("properties")
                    if extra_props:
                        import json
                        try:
                            properties.update(json.loads(extra_props))
                        except:
                            pass
                            
                    payload = {"properties": properties}
                    
                    url = f"{base_url}/contacts"
                    async with session.post(url, headers=headers, json=payload) as resp:
                         if resp.status != 201:
                            error_text = await resp.text()
                            return {"status": "error", "error": f"HubSpot API Error {resp.status}: {error_text}"}
                         res_data = await resp.json()
                         return {"status": "success", "data": {"result": res_data}}
                
                elif action == "list_contacts":
                    url = f"{base_url}/contacts"
                    async with session.get(url, headers=headers) as resp:
                         res_data = await resp.json()
                         return {"status": "success", "data": {"result": res_data.get("results", [])}}

            return {"status": "error", "error": f"Unsupported action: {action}"}

        except Exception as e:
            return {"status": "error", "error": f"HubSpot Node Failed: {str(e)}"}