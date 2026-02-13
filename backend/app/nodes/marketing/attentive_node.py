"""
Attentive Node - Studio Standard
Batch 62: Marketing Automation
"""
from typing import Any, Dict, Optional, List
import aiohttp
from ...base import BaseNode
from ...registry import register_node

@register_node("attentive_node")
class AttentiveNode(BaseNode):
    """
    Automate SMS marketing and subscriber management via Attentive.
    Optimized for mobile-first engagement.
    """
    node_type = "attentive_node"
    version = "1.0.0"
    category = "marketing"
    credentials_required = ["attentive_auth"]

    inputs = {
        "action": {
            "type": "dropdown",
            "default": "list_subscribers",
            "options": ["list_subscribers", "get_subscriber", "create_subscriber", "trigger_event"],
            "description": "Attentive action"
        },
        "email": {
            "type": "string",
            "optional": True,
            "description": "Subscriber email"
        },
        "phone": {
            "type": "string",
            "optional": True,
            "description": "Subscriber phone number (E.164 format)"
        },
        "event_type": {
            "type": "string",
            "optional": True,
            "description": "Event type (e.g. 'purchase')"
        }
    }

    outputs = {
        "result": {"type": "any"},
        "status": {"type": "string"},
        "count": {"type": "number"}
    }

    async def execute(self, input_data: Any, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        try:
            # 1. Resolve Auth
            creds = await self.get_credential("attentive_auth")
            api_token = creds.get("api_token") if creds else self.get_config("api_token")
            
            if not api_token:
                return {"status": "error", "error": "Attentive API Token is required."}

            headers = {
                "Authorization": f"Bearer {api_token}",
                "Content-Type": "application/json",
                "Accept": "application/json"
            }
            
            base_url = "https://api.attentivemobile.com/v1"
            action = self.get_config("action", "list_subscribers")

            async with aiohttp.ClientSession() as session:
                if action == "list_subscribers":
                    url = f"{base_url}/subscribers"
                    async with session.get(url, headers=headers) as resp:
                        res_data = await resp.json()
                        return {"status": "success", "data": {"result": res_data, "count": len(res_data) if isinstance(res_data, list) else 1}}

                elif action == "create_subscriber":
                    url = f"{base_url}/subscribers"
                    email = self.get_config("email")
                    phone = self.get_config("phone") or str(input_data)
                    
                    payload = {
                        "user": {
                            "phone": phone,
                            "email": email
                        },
                        "signUpSourceId": "standard_studio_node" # Placeholder
                    }
                    async with session.post(url, headers=headers, json=payload) as resp:
                        res_data = await resp.json()
                        return {"status": "success", "data": {"result": res_data, "status": "subscribed"}}

                elif action == "trigger_event":
                    url = f"{base_url}/events/custom"
                    email = self.get_config("email")
                    phone = self.get_config("phone")
                    event_type = self.get_config("event_type") or str(input_data)
                    
                    payload = {
                        "type": event_type,
                        "user": {
                            "phone": phone,
                            "email": email
                        },
                        "properties": {}
                    }
                    async with session.post(url, headers=headers, json=payload) as resp:
                        res_data = await resp.json()
                        return {"status": "success", "data": {"result": res_data}}

                return {"status": "error", "error": f"Unsupported Attentive action: {action}"}

        except Exception as e:
            return {"status": "error", "error": f"Attentive Node Failed: {str(e)}"}
