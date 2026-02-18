"""
Heap Node - Studio Standard (Universal Method)
Batch 98: Analytics (Enterprise Expansion)
"""
from typing import Any, Dict, Optional, List
import aiohttp
from ..base import BaseNode
from ..registry import register_node

@register_node("heap_node")
class HeapNode(BaseNode):
    """
    Track events and identify users in Heap Analytics.
    """
    node_type = "heap_node"
    version = "1.0.0"
    category = "analytics"
    credentials_required = ["heap_auth"]


    properties = [
        {
            'displayName': 'Operation',
            'name': 'operation',
            'type': 'options',
            'default': 'track_event',
            'options': [
                {'name': 'Track Event', 'value': 'track_event'},
                {'name': 'Add User Properties', 'value': 'add_user_properties'},
            ],
            'description': 'Heap action',
        },
        {
            'displayName': 'Event Name',
            'name': 'event_name',
            'type': 'string',
            'default': '',
        },
        {
            'displayName': 'Identity',
            'name': 'identity',
            'type': 'string',
            'default': '',
            'description': 'User Identity',
            'required': True,
        },
        {
            'displayName': 'Properties',
            'name': 'properties',
            'type': 'string',
            'default': '',
            'description': 'JSON properties',
        },
    ]
    inputs = {
        "action": {
            "type": "dropdown",
            "default": "track_event",
            "options": ["track_event", "add_user_properties"],
            "description": "Heap action"
        },
        "identity": {
            "type": "string",
            "required": True,
            "description": "User Identity"
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
            creds = await self.get_credential("heap_auth")
            app_id = creds.get("app_id")
            
            if not app_id:
                return {"status": "error", "error": "Heap App ID required."}

            headers = {
                "Content-Type": "application/json",
                "Accept": "application/json"
            }
            
            # 2. Connect to Real API
            base_url = "https://heapanalytics.com/api"
            action = self.get_config("action", "track_event")

            identity = self.get_config("identity")
            import json
            props_str = self.get_config("properties", "{}")
            props = json.loads(props_str) if isinstance(props_str, str) else props_str

            async with aiohttp.ClientSession() as session:
                if action == "track_event":
                    event = self.get_config("event_name")
                    if not event:
                        return {"status": "error", "error": "event_name required"}

                    url = f"{base_url}/track"
                    payload = {
                        "app_id": app_id,
                        "identity": identity,
                        "event": event,
                        "properties": props
                    }
                    async with session.post(url, headers=headers, json=payload) as resp:
                        # Heap API returns 200 OK even on some errors, check response?
                        # Docs say 200 OK on success
                        if resp.status != 200:
                            return {"status": "error", "error": f"Heap API Error: {resp.status}"}
                        # No content returned usually
                        return {"status": "success", "data": {"result": {"message": "Event tracked"}}}

                elif action == "add_user_properties":
                    url = f"{base_url}/add_user_properties"
                    payload = {
                        "app_id": app_id,
                        "identity": identity,
                        "properties": props
                    }
                    async with session.post(url, headers=headers, json=payload) as resp:
                        if resp.status != 200:
                            return {"status": "error", "error": f"Heap API Error: {resp.status}"}
                        return {"status": "success", "data": {"result": {"message": "Properties added"}}}

                return {"status": "error", "error": f"Unsupported action: {action}"}

        except Exception as e:
            return {"status": "error", "error": f"Heap Node Failed: {str(e)}"}