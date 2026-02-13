"""
Klaviyo Node - Studio Standard
Batch 62: Marketing Automation
"""
from typing import Any, Dict, Optional, List
import aiohttp
from ...base import BaseNode
from ...registry import register_node

@register_node("klaviyo_node")
class KlaviyoNode(BaseNode):
    """
    Automate e-commerce marketing and customer events via Klaviyo.
    Supports profile management, events, and metrics.
    """
    node_type = "klaviyo_node"
    version = "1.0.0"
    category = "marketing"
    credentials_required = ["klaviyo_auth"]

    inputs = {
        "action": {
            "type": "dropdown",
            "default": "get_profiles",
            "options": ["get_profiles", "create_profile", "create_event", "get_metrics"],
            "description": "Klaviyo action"
        },
        "email": {
            "type": "string",
            "optional": True,
            "description": "Customer email"
        },
        "event_name": {
            "type": "string",
            "optional": True,
            "description": "Metric name for event (e.g. 'Viewed Product')"
        },
        "properties": {
            "type": "json",
            "optional": True,
            "description": "Properties for profile or event"
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
            creds = await self.get_credential("klaviyo_auth")
            api_key = creds.get("api_key") if creds else self.get_config("api_key")
            
            if not api_key:
                return {"status": "error", "error": "Klaviyo Private API Key is required."}

            headers = {
                "Authorization": f"Klaviyo-API-Key {api_key}",
                "Accept": "application/json",
                "Content-Type": "application/json",
                "revision": "2024-02-15" # Latest Klaviyo revision
            }
            
            base_url = "https://a.klaviyo.com/api"
            action = self.get_config("action", "get_profiles")

            async with aiohttp.ClientSession() as session:
                if action == "get_profiles":
                    url = f"{base_url}/profiles"
                    async with session.get(url, headers=headers) as resp:
                        res_data = await resp.json()
                        data = res_data.get("data", [])
                        return {"status": "success", "data": {"result": data, "count": len(data)}}

                elif action == "create_profile":
                    url = f"{base_url}/profiles"
                    email = self.get_config("email") or str(input_data)
                    props = self.get_config("properties", {})
                    payload = {
                        "data": {
                            "type": "profile",
                            "attributes": {
                                "email": email,
                                "properties": props
                            }
                        }
                    }
                    async with session.post(url, headers=headers, json=payload) as resp:
                        res_data = await resp.json()
                        return {"status": "success", "data": {"result": res_data, "status": "created"}}

                elif action == "create_event":
                    url = f"{base_url}/events"
                    email = self.get_config("email")
                    event_name = self.get_config("event_name")
                    props = self.get_config("properties", {})
                    
                    payload = {
                        "data": {
                            "type": "event",
                            "attributes": {
                                "metric": {"name": event_name},
                                "profile": {"email": email},
                                "properties": props
                            }
                        }
                    }
                    async with session.post(url, headers=headers, json=payload) as resp:
                        res_data = await resp.json()
                        return {"status": "success", "data": {"result": res_data, "status": "recorded"}}

                return {"status": "error", "error": f"Unsupported Klaviyo action: {action}"}

        except Exception as e:
            return {"status": "error", "error": f"Klaviyo Node Failed: {str(e)}"}
