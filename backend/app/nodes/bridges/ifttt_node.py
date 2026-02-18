"""
IFTTT Node - Studio Standard (Universal Method)
Batch 101: Automation Bridges (Interoperability)
"""
from typing import Any, Dict, Optional, List
import aiohttp
from ..base import BaseNode
from ..registry import register_node

@register_node("ifttt_node")
class IFTTTNode(BaseNode):
    """
    Trigger IFTTT Applets via Webhooks Service (Maker Webhooks).
    """
    node_type = "ifttt_node"
    version = "1.0.0"
    category = "bridges"
    credentials_required = ["ifttt_auth"]


    properties = [
        {
            'displayName': 'Event Name',
            'name': 'event_name',
            'type': 'string',
            'default': '',
            'description': 'The Event Name defined in IFTTT',
            'required': True,
        },
        {
            'displayName': 'Value1',
            'name': 'value1',
            'type': 'string',
            'default': '',
            'description': 'Value 1',
        },
        {
            'displayName': 'Value2',
            'name': 'value2',
            'type': 'string',
            'default': '',
            'description': 'Value 2',
        },
        {
            'displayName': 'Value3',
            'name': 'value3',
            'type': 'string',
            'default': '',
            'description': 'Value 3',
        },
    ]
    inputs = {
        "event_name": {
            "type": "string",
            "required": True,
            "description": "The Event Name defined in IFTTT"
        },
        "value1": {
            "type": "string",
            "optional": True,
            "description": "Value 1"
        },
        "value2": {
            "type": "string",
            "optional": True,
            "description": "Value 2"
        },
        "value3": {
            "type": "string",
            "optional": True,
            "description": "Value 3"
        }
    }

    outputs = {
        "result": {"type": "any"},
        "status": {"type": "string"}
    }

    async def execute(self, input_data: Any, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        try:
            creds = await self.get_credential("ifttt_auth")
            key = creds.get("webhook_key")
            
            if not key:
                return {"status": "error", "error": "IFTTT Webhook Key required."}
            
            event = self.get_config("event_name")
            if not event:
                 return {"status": "error", "error": "event_name required"}

            v1 = self.get_config("value1", "")
            v2 = self.get_config("value2", "")
            v3 = self.get_config("value3", "")
            
            url = f"https://maker.ifttt.com/trigger/{event}/with/key/{key}"
            
            payload = {"value1": v1, "value2": v2, "value3": v3}
            
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=payload) as resp:
                    text = await resp.text()
                    if resp.status != 200:
                         return {"status": "error", "error": f"IFTTT Error: {resp.status} - {text}"}
                    
                    return {
                        "status": "success",
                        "data": {
                            "result": {"message": text}
                        }
                    }

        except Exception as e:
            return {"status": "error", "error": f"IFTTT Node Failed: {str(e)}"}