"""
Luma Events Node - Studio Standard
Batch 68: Event Management
"""
from typing import Any, Dict, Optional, List
import aiohttp
from ...base import BaseNode
from ...registry import register_node

@register_node("luma_events_node")
class LumaEventsNode(BaseNode):
    """
    Automate community events and guest lists via Luma (lu.ma) API.
    """
    node_type = "luma_events_node"
    version = "1.0.0"
    category = "events"
    credentials_required = ["luma_auth"]

    inputs = {
        "action": {
            "type": "dropdown",
            "default": "list_events",
            "options": ["list_events", "get_event", "list_guests"],
            "description": "Luma action"
        },
        "event_api_id": {
            "type": "string",
            "optional": True,
            "description": "Unique API ID of the event"
        }
    }

    outputs = {
        "result": {"type": "any"},
        "status": {"type": "string"},
        "count": {"type": "number"}
    }

    async def execute(self, input_data: Any, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        try:
            creds = await self.get_credential("luma_auth")
            api_key = creds.get("api_key") if creds else self.get_config("api_key")
            
            if not api_key:
                return {"status": "error", "error": "Luma API Key is required."}

            headers = {
                "x-luma-api-key": api_key,
                "Accept": "application/json"
            }
            
            base_url = "https://api.lu.ma/v1"
            action = self.get_config("action", "list_events")

            async with aiohttp.ClientSession() as session:
                if action == "list_events":
                    url = f"{base_url}/event/list"
                    async with session.get(url, headers=headers) as resp:
                        res_data = await resp.json()
                        entries = res_data.get("entries", [])
                        return {"status": "success", "data": {"result": entries, "count": len(entries)}}

                elif action == "get_event":
                    e_id = self.get_config("event_api_id") or str(input_data)
                    url = f"{base_url}/event/get"
                    params = {"api_id": e_id}
                    async with session.get(url, headers=headers, params=params) as resp:
                        res_data = await resp.json()
                        return {"status": "success", "data": {"result": res_data}}

                elif action == "list_guests":
                    e_id = self.get_config("event_api_id")
                    url = f"{base_url}/event/get-guests"
                    params = {"api_id": e_id}
                    async with session.get(url, headers=headers, params=params) as resp:
                        res_data = await resp.json()
                        guests = res_data.get("guests", [])
                        return {"status": "success", "data": {"result": guests, "count": len(guests)}}

                return {"status": "error", "error": f"Unsupported Luma action: {action}"}

        except Exception as e:
            return {"status": "error", "error": f"Luma Events Node Failed: {str(e)}"}
