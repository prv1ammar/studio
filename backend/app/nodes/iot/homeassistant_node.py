"""
Home Assistant Control Node - Studio Standard (Universal Method)
"""
from typing import Any, Dict, Optional
import aiohttp
from ..base import BaseNode
from ..registry import register_node

@register_node("homeassistant_control")
class HomeAssistantControlNode(BaseNode):
    """
    Control Home Assistant devices (turn on/off/toggle).
    """
    node_type = "homeassistant_control"
    version = "1.0.0"
    category = "iot"
    credentials_required = ["homeassistant_auth"]


    properties = [
        {
            'displayName': 'Operation',
            'name': 'operation',
            'type': 'options',
            'default': 'toggle',
            'options': [
                {'name': 'Turn On', 'value': 'turn_on'},
                {'name': 'Turn Off', 'value': 'turn_off'},
                {'name': 'Toggle', 'value': 'toggle'},
            ],
            'description': 'Service action to perform',
        },
        {
            'displayName': 'Entity Id',
            'name': 'entity_id',
            'type': 'string',
            'default': '',
            'description': 'Entity ID to control (e.g., switch.living_room, light.kitchen)',
            'required': True,
        },
    ]
    inputs = {
        "entity_id": {
            "type": "string",
            "required": True,
            "description": "Entity ID to control (e.g., switch.living_room, light.kitchen)"
        },
        "action": {
            "type": "dropdown",
            "default": "toggle",
            "options": ["turn_on", "turn_off", "toggle"],
            "description": "Service action to perform"
        }
    }

    outputs = {
        "result": {"type": "dict"},
        "status": {"type": "string"}
    }

    async def execute(self, input_data: Any, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        try:
            creds = await self.get_credential("homeassistant_auth")
            token = creds.get("token")
            base_url = creds.get("base_url")
            
            if not token or not base_url:
                return {"status": "error", "error": "Home Assistant Token and Base URL are required"}

            entity_id = self.get_config("entity_id") or str(input_data)
            action = self.get_config("action", "toggle")
            
            domain = entity_id.split(".")[0]
            url = f"{base_url.rstrip('/')}/api/services/{domain}/{action}"

            headers = {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
            }
            payload = {"entity_id": entity_id}

            async with aiohttp.ClientSession() as session:
                async with session.post(url, headers=headers, json=payload) as response:
                    if response.status != 200:
                        text = await response.text()
                        return {"status": "error", "error": f"Home Assistant API error {response.status}: {text}"}
                    
                    data = await response.json()

            return {
                "status": "success",
                "data": {
                    "result": data
                }
            }

        except Exception as e:
            return {"status": "error", "error": f"Home Assistant Control Failed: {str(e)}"}