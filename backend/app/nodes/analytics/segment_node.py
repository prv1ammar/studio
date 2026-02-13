"""
Segment Node - Studio Standard (Universal Method)
Batch 98: Analytics (Enterprise Expansion)
"""
from typing import Any, Dict, Optional, List
import aiohttp
from ...base import BaseNode
from ...registry import register_node

@register_node("segment_node")
class SegmentNode(BaseNode):
    """
    Collect, clean, and send customer data via Segment API.
    """
    node_type = "segment_node"
    version = "1.0.0"
    category = "analytics"
    credentials_required = ["segment_auth"]

    inputs = {
        "action": {
            "type": "dropdown",
            "default": "track_event",
            "options": ["track_event", "identify_user", "group_user", "page_view", "screen_view"],
            "description": "Segment action"
        },
        "event_name": {
            "type": "string",
            "optional": True
        },
        "user_id": {
            "type": "string",
            "description": "User ID"
        },
        "properties": {
            "type": "string",
            "optional": True,
            "description": "JSON properties/traits"
        }
    }

    outputs = {
        "result": {"type": "any"},
        "status": {"type": "string"}
    }

    async def execute(self, input_data: Any, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        try:
            # 1. Authentication
            creds = await self.get_credential("segment_auth")
            write_key = creds.get("write_key")
            
            if not write_key:
                return {"status": "error", "error": "Segment Write Key required."}

            auth = aiohttp.BasicAuth(write_key, "")
            
            # 2. Connect to Real API
            base_url = "https://api.segment.io/v1"
            action = self.get_config("action", "track_event")
            
            # Common params
            user_id = self.get_config("user_id")
            
            import json
            props_str = self.get_config("properties")
            props = {}
            if props_str:
                 props = json.loads(props_str) if isinstance(props_str, str) else props_str

            if not user_id:
                 return {"status": "error", "error": "user_id required"}

            async with aiohttp.ClientSession(auth=auth) as session:
                
                if action == "track_event":
                    event = self.get_config("event_name")
                    if not event:
                        return {"status": "error", "error": "event_name required"}

                    url = f"{base_url}/track"
                    payload = {
                        "userId": user_id,
                        "event": event,
                        "properties": props
                    }
                    async with session.post(url, json=payload) as resp:
                        if resp.status != 200:
                            return {"status": "error", "error": f"Segment API Error: {resp.status}"}
                        # Typically returns {success: true}
                        res_data = await resp.json()
                        return {"status": "success", "data": {"result": res_data}}

                elif action == "identify_user":
                    url = f"{base_url}/identify"
                    payload = {
                        "userId": user_id,
                        "traits": props
                    }
                    async with session.post(url, json=payload) as resp:
                        if resp.status != 200:
                            return {"status": "error", "error": f"Segment API Error: {resp.status}"}
                        res_data = await resp.json()
                        return {"status": "success", "data": {"result": res_data}}

                elif action == "group_user":
                    group_id = self.get_config("event_name") # Reusing event_name field as group_id
                    if not group_id:
                         return {"status": "error", "error": "group_id (in event_name) required"}
                    
                    url = f"{base_url}/group"
                    payload = {
                        "userId": user_id,
                        "groupId": group_id,
                        "traits": props
                    }
                    async with session.post(url, json=payload) as resp:
                        if resp.status != 200:
                            return {"status": "error", "error": f"Segment API Error: {resp.status}"}
                        res_data = await resp.json()
                        return {"status": "success", "data": {"result": res_data}}

                elif action == "page_view":
                    page_name = self.get_config("event_name") # Reusing event_name
                    
                    url = f"{base_url}/page"
                    payload = {
                        "userId": user_id,
                        "name": page_name,
                        "properties": props
                    }
                    async with session.post(url, json=payload) as resp:
                         if resp.status != 200:
                              return {"status": "error", "error": f"Segment API Error: {resp.status}"}
                         res_data = await resp.json()
                         return {"status": "success", "data": {"result": res_data}}
                         
                return {"status": "error", "error": f"Unsupported action: {action}"}

        except Exception as e:
            return {"status": "error", "error": f"Segment Node Failed: {str(e)}"}
