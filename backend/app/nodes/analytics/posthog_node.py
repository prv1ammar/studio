"""
PostHog Node - Studio Standard (Universal Method)
Batch 109: Analytics & Support
"""
from typing import Any, Dict, Optional
import aiohttp
from ...base import BaseNode
from ...registry import register_node

@register_node("posthog_node")
class PostHogNode(BaseNode):
    """
    PostHog integration for product analytics.
    """
    node_type = "posthog_node"
    version = "1.0.0"
    category = "analytics"
    credentials_required = ["posthog_auth"]

    inputs = {
        "action": {
            "type": "dropdown",
            "default": "capture_event",
            "options": ["capture_event", "identify_user"],
            "description": "PostHog action"
        },
        "event": {
            "type": "string",
            "optional": True
        },
        "distinct_id": {
            "type": "string",
            "optional": True
        },
        "properties": {
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
            creds = await self.get_credential("posthog_auth")
            api_key = creds.get("api_key")
            host = creds.get("host", "https://app.posthog.com")
            
            if not api_key:
                return {"status": "error", "error": "PostHog API key required"}

            base_url = f"{host}/capture"
            headers = {"Content-Type": "application/json"}
            
            action = self.get_config("action", "capture_event")

            async with aiohttp.ClientSession() as session:
                if action == "capture_event":
                    event = self.get_config("event")
                    distinct_id = self.get_config("distinct_id")
                    
                    if not event or not distinct_id:
                        return {"status": "error", "error": "event and distinct_id required"}
                    
                    payload = {
                        "api_key": api_key,
                        "event": event,
                        "properties": {
                            "distinct_id": distinct_id
                        },
                        "timestamp": None # Optional
                    }
                    
                    # Merge extra props
                    import json
                    extra_props = self.get_config("properties")
                    if extra_props:
                        try:
                            payload["properties"].update(json.loads(extra_props))
                        except:
                            pass
                            
                    async with session.post(base_url, headers=headers, json=payload) as resp:
                         # PostHog usually returns status 1 or 200/201
                         if resp.status != 200:
                            error_text = await resp.text()
                            return {"status": "error", "error": f"PostHog API Error {resp.status}: {error_text}"}
                         res_data = await resp.json()
                         return {"status": "success", "data": {"result": res_data}}

                elif action == "identify_user":
                    distinct_id = self.get_config("distinct_id")
                    if not distinct_id: return {"status": "error", "error": "distinct_id required"}
                    
                    payload = {
                        "api_key": api_key,
                        "event": "$identify",
                        "properties": {
                            "distinct_id": distinct_id,
                            "$set": {}
                        }
                    }
                    extra_props = self.get_config("properties")
                    if extra_props:
                        try:
                           payload["properties"]["$set"] = json.loads(extra_props)
                        except:
                           pass
                           
                    async with session.post(base_url, headers=headers, json=payload) as resp:
                         res_data = await resp.json()
                         return {"status": "success", "data": {"result": res_data}}

            return {"status": "error", "error": f"Unsupported action: {action}"}

        except Exception as e:
            return {"status": "error", "error": f"PostHog Node Failed: {str(e)}"}
