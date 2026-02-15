"""
Mixpanel Node - Studio Standard (Universal Method)
Batch 109: Analytics & Support
"""
from typing import Any, Dict, Optional
import aiohttp
from ...base import BaseNode
from ...registry import register_node

@register_node("mixpanel_node")
class MixpanelNode(BaseNode):
    """
    Mixpanel integration for product analytics.
    """
    node_type = "mixpanel_node"
    version = "1.0.0"
    category = "analytics"
    credentials_required = ["mixpanel_auth"]

    inputs = {
        "action": {
            "type": "dropdown",
            "default": "track_event",
            "options": ["track_event", "profile_set", "profile_delete"],
            "description": "Mixpanel action"
        },
        "event_name": {
            "type": "string",
            "optional": True
        },
        "distinct_id": {
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
            creds = await self.get_credential("mixpanel_auth")
            project_token = creds.get("project_token")
            api_secret = creds.get("api_secret")
            
            if not project_token:
                return {"status": "error", "error": "Mixpanel project token required"}

            base_url = "https://api.mixpanel.com"
            headers = {"Accept": "text/plain", "Content-Type": "application/x-www-form-urlencoded"}
            
            action = self.get_config("action", "track_event")

            async with aiohttp.ClientSession() as session:
                if action == "track_event":
                    event_name = self.get_config("event_name")
                    distinct_id = self.get_config("distinct_id")
                    
                    if not event_name or not distinct_id:
                        return {"status": "error", "error": "event_name and distinct_id required"}
                        
                    import json
                    payload = {
                        "event": event_name,
                        "properties": {
                            "distinct_id": distinct_id,
                            "token": project_token
                            # Add extra properties logic here
                        }
                    }
                    import base64
                    data = f"data={base64.b64encode(json.dumps(payload).encode()).decode()}"
                    
                    async with session.post(f"{base_url}/track", headers=headers, data=data) as resp:
                         # Mixpanel returns 1 for success
                         res_text = await resp.text()
                         if res_text != "1":
                             return {"status": "error", "error": f"Mixpanel Error: {res_text}"}
                         return {"status": "success", "data": {"result": res_text}}

                elif action == "profile_set":
                    # Assume $set operation
                    url = f"{base_url}/engage"
                    distinct_id = self.get_config("distinct_id")
                    payload = {
                        "$token": project_token,
                        "$distinct_id": distinct_id,
                        "$set": {"last_seen": "now"} # Simplified
                    }
                    import base64
                    data = f"data={base64.b64encode(json.dumps(payload).encode()).decode()}"
                    async with session.post(url, headers=headers, data=data) as resp:
                        res_text = await resp.text()
                        return {"status": "success", "data": {"result": res_text}}

            return {"status": "error", "error": f"Unsupported action: {action}"}

        except Exception as e:
            return {"status": "error", "error": f"Mixpanel Node Failed: {str(e)}"}
