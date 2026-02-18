"""
Pipedrive Node - Studio Standard (Universal Method)
Batch 108: Marketing & CRM
"""
from typing import Any, Dict, Optional
import aiohttp
from ..base import BaseNode
from ..registry import register_node

@register_node("pipedrive_node")
class PipedriveNode(BaseNode):
    """
    Pipedrive CRM integration for deal management.
    """
    node_type = "pipedrive_node"
    version = "1.0.0"
    category = "marketing"
    credentials_required = ["pipedrive_auth"]


    properties = [
        {
            'displayName': 'Operation',
            'name': 'operation',
            'type': 'options',
            'default': 'create_deal',
            'options': [
                {'name': 'Create Deal', 'value': 'create_deal'},
                {'name': 'Create Person', 'value': 'create_person'},
                {'name': 'Get Deal', 'value': 'get_deal'},
                {'name': 'Create Activity', 'value': 'create_activity'},
            ],
            'description': 'Pipedrive action',
        },
        {
            'displayName': 'Currency',
            'name': 'currency',
            'type': 'string',
            'default': 'USD',
        },
        {
            'displayName': 'Title',
            'name': 'title',
            'type': 'string',
            'default': '',
        },
        {
            'displayName': 'Value',
            'name': 'value',
            'type': 'string',
            'default': '',
        },
    ]
    inputs = {
        "action": {
            "type": "dropdown",
            "default": "create_deal",
            "options": ["create_deal", "create_person", "get_deal", "create_activity"],
            "description": "Pipedrive action"
        },
        "title": {
            "type": "string",
            "optional": True
        },
        "value": {
            "type": "number",
            "optional": True
        },
        "currency": {
            "type": "string",
            "default": "USD",
            "optional": True
        }
    }

    outputs = {
        "result": {"type": "any"},
        "status": {"type": "string"}
    }

    async def execute(self, input_data: Any, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        try:
            creds = await self.get_credential("pipedrive_auth")
            api_token = creds.get("api_token")
            # Or access_token if using OAuth
            
            if not api_token:
                return {"status": "error", "error": "Pipedrive API token required"}

            base_url = "https://api.pipedrive.com/v1"
            params = {"api_token": api_token}
            
            action = self.get_config("action", "create_deal")

            async with aiohttp.ClientSession() as session:
                if action == "create_deal":
                    title = self.get_config("title")
                    value = self.get_config("value")
                    currency = self.get_config("currency", "USD")
                    
                    if not title:
                         return {"status": "error", "error": "title required"}
                         
                    payload = {
                        "title": title,
                        "value": value,
                        "currency": currency
                    }
                    
                    url = f"{base_url}/deals"
                    async with session.post(url, params=params, json=payload) as resp:
                         if resp.status != 201:
                            error_text = await resp.text()
                            return {"status": "error", "error": f"Pipedrive API Error {resp.status}: {error_text}"}
                         res_data = await resp.json()
                         return {"status": "success", "data": {"result": res_data.get("data")}}
                
                elif action == "create_person":
                     name = self.get_config("name") # Reuse title or add input
                     name = name if name else title
                     if not name:
                         return {"status": "error", "error": "Name (title input) required"}
                         
                     payload = {"name": name}
                     url = f"{base_url}/persons"
                     async with session.post(url, params=params, json=payload) as resp:
                         res_data = await resp.json()
                         return {"status": "success", "data": {"result": res_data.get("data")}}

            return {"status": "error", "error": f"Unsupported action: {action}"}

        except Exception as e:
            return {"status": "error", "error": f"Pipedrive Node Failed: {str(e)}"}