"""
Segment Node - Studio Standard (Universal Method)
Batch 109: Analytics & Support
"""
from typing import Any, Dict, Optional
import aiohttp
from ...base import BaseNode
from ...registry import register_node

@register_node("segment_node")
class SegmentNode(BaseNode):
    """
    Segment (Twilio) integration for customer data platform.
    """
    node_type = "segment_node"
    version = "1.0.0"
    category = "analytics"
    credentials_required = ["segment_auth"]

    inputs = {
        "action": {
            "type": "dropdown",
            "default": "track_event",
            "options": ["track_event", "identify_user"],
            "description": "Segment action"
        },
        "event": {
            "type": "string",
            "optional": True
        },
        "user_id": {
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
            creds = await self.get_credential("segment_auth")
            write_key = creds.get("write_key")
            
            if not write_key:
                return {"status": "error", "error": "Segment Write Key required"}

            base_url = "https://api.segment.io/v1"
            auth = aiohttp.BasicAuth(write_key, "") # Username = write_key, password blank
            headers = {"Content-Type": "application/json"}
            
            action = self.get_config("action", "track_event")

            async with aiohttp.ClientSession() as session:
                if action == "track_event":
                    event = self.get_config("event")
                    user_id = self.get_config("user_id")
                    
                    if not event or not user_id:
                        return {"status": "error", "error": "event and user_id required"}
                    
                    import json
                    payload = {
                        "event": event,
                        "userId": user_id,
                        "properties": {}
                    }
                    extra_props = self.get_config("properties")
                    if extra_props:
                        try:
                           payload["properties"] = json.loads(extra_props)
                        except:
                           pass
                           
                    url = f"{base_url}/track"
                    async with session.post(url, headers=headers, auth=auth, json=payload) as resp:
                         # Segment responds 200 OK often
                         if resp.status != 200:
                            error_text = await resp.text()
                            return {"status": "error", "error": f"Segment API Error {resp.status}: {error_text}"}
                         res_data = await resp.json()
                         return {"status": "success", "data": {"result": res_data}}
                
                elif action == "identify_user":
                    user_id = self.get_config("user_id")
                    if not user_id: return {"status": "error", "error": "user_id required"}
                    
                    payload = {
                        "userId": user_id,
                        "traits": {}
                    }
                    extra_props = self.get_config("properties") # Using properties input for traits
                    if extra_props:
                        try:
                           payload["traits"] = json.loads(extra_props)
                        except:
                           pass
                           
                    url = f"{base_url}/identify"
                    async with session.post(url, headers=headers, auth=auth, json=payload) as resp:
                         res_data = await resp.json()
                         return {"status": "success", "data": {"result": res_data}}

            return {"status": "error", "error": f"Unsupported action: {action}"}

        except Exception as e:
            return {"status": "error", "error": f"Segment Node Failed: {str(e)}"}
