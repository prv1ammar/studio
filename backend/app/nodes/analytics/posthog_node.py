"""
PostHog Node - Studio Standard (Universal Method)
Batch 98: Analytics (Enterprise Expansion)
"""
from typing import Any, Dict, Optional, List
import aiohttp
from ...base import BaseNode
from ...registry import register_node

@register_node("posthog_node")
class PostHogNode(BaseNode):
    """
    Capture events and identify users in PostHog.
    """
    node_type = "posthog_node"
    version = "1.0.0"
    category = "analytics"
    credentials_required = ["posthog_auth"]

    inputs = {
        "action": {
            "type": "dropdown",
            "default": "capture_event",
            "options": ["capture_event", "identify_user", "alias_user"],
            "description": "PostHog action"
        },
        "distinct_id": {
            "type": "string",
            "required": True,
            "description": "User Distinct ID"
        },
        "event_name": {
            "type": "string",
            "optional": True
        },
        "properties": {
            "type": "string",
            "optional": True,
            "description": "JSON properties"
        }
    }

    outputs = {
        "result": {"type": "any"},
        "status": {"type": "string"}
    }

    async def execute(self, input_data: Any, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        try:
            # 1. Authentication
            creds = await self.get_credential("posthog_auth")
            api_key = creds.get("api_key") # Project API Key
            host = creds.get("host", "https://app.posthog.com")
            
            if not api_key:
                return {"status": "error", "error": "PostHog API Key required."}

            headers = {
                "Content-Type": "application/json"
            }
            
            # 2. Connect to Real API
            base_url = f"{host.rstrip('/')}"
            action = self.get_config("action", "capture_event")
            distinct_id = self.get_config("distinct_id")
            
            import json
            props_str = self.get_config("properties")
            props = {}
            if props_str:
                props = json.loads(props_str) if isinstance(props_str, str) else props_str

            async with aiohttp.ClientSession() as session:
                
                if action == "capture_event":
                    event = self.get_config("event_name")
                    if not event:
                        return {"status": "error", "error": "event_name required"}

                    url = f"{base_url}/capture/"
                    payload = {
                        "api_key": api_key,
                        "event": event,
                        "properties": {
                            "distinct_id": distinct_id,
                            **props
                        },
                        "timestamp": None # Optional
                    }
                    async with session.post(url, headers=headers, json=payload) as resp:
                        if resp.status != 200:
                            return {"status": "error", "error": f"PostHog API Error: {resp.status}"}
                        res_data = await resp.json()
                        return {"status": "success", "data": {"result": res_data}}

                elif action == "identify_user":
                    url = f"{base_url}/capture/"
                    payload = {
                        "api_key": api_key,
                        "event": "$identify",
                        "properties": {
                            "distinct_id": distinct_id,
                            "$set": props
                        }
                    }
                    async with session.post(url, headers=headers, json=payload) as resp:
                         if resp.status != 200:
                              return {"status": "error", "error": f"PostHog API Error: {resp.status}"}
                         res_data = await resp.json()
                         return {"status": "success", "data": {"result": res_data}}

                elif action == "alias_user":
                    alias_id = self.get_config("event_name") # Reusing event_name for alias (new ID)
                    if not alias_id:
                         return {"status": "error", "error": "alias_id (in event_name) required"}
                    
                    url = f"{base_url}/capture/"
                    # Alias: alias_id is the new ID, distinct_id is the old ID
                    payload = {
                        "api_key": api_key,
                        "event": "$create_alias",
                        "properties": {
                            "distinct_id": distinct_id,
                            "alias": alias_id
                        }
                    }
                    async with session.post(url, headers=headers, json=payload) as resp:
                         if resp.status != 200:
                              return {"status": "error", "error": f"PostHog API Error: {resp.status}"}
                         res_data = await resp.json()
                         return {"status": "success", "data": {"result": res_data}}

                return {"status": "error", "error": f"Unsupported action: {action}"}

        except Exception as e:
            return {"status": "error", "error": f"PostHog Node Failed: {str(e)}"}
