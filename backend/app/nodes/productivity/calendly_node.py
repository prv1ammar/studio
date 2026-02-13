"""
Calendly Node - Studio Standard (Universal Method)
Batch 91: Productivity Suite (n8n Critical)
"""
from typing import Any, Dict, Optional, List
import aiohttp
from ...base import BaseNode
from ...registry import register_node

@register_node("calendly_node")
class CalendlyNode(BaseNode):
    """
    Manage scheduling and events via Calendly API.
    """
    node_type = "calendly_node"
    version = "1.0.0"
    category = "productivity"
    credentials_required = ["calendly_auth"]

    inputs = {
        "action": {
            "type": "dropdown",
            "default": "list_events",
            "options": ["list_events", "get_event", "list_event_types", "get_user"],
            "description": "Calendly action"
        },
        "event_uuid": {
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
            # 1. Authentication
            creds = await self.get_credential("calendly_auth")
            api_key = creds.get("api_key")
            
            if not api_key:
                return {"status": "error", "error": "Calendly API Key required."}

            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            }
            
            # 2. Connect to Real API
            base_url = "https://api.calendly.com"
            action = self.get_config("action", "list_events")

            async with aiohttp.ClientSession() as session:
                if action == "get_user":
                    url = f"{base_url}/users/me"
                    async with session.get(url, headers=headers) as resp:
                        if resp.status != 200:
                            return {"status": "error", "error": f"Calendly Error: {resp.status}"}
                        res_data = await resp.json()
                        return {"status": "success", "data": {"result": res_data.get("resource", {})}}

                elif action == "list_events":
                    # First get user to get organization
                    url = f"{base_url}/users/me"
                    async with session.get(url, headers=headers) as resp:
                        if resp.status != 200:
                            return {"status": "error", "error": f"Calendly Error: {resp.status}"}
                        user_data = await resp.json()
                        user_uri = user_data.get("resource", {}).get("uri")
                    
                    # Now get events
                    url = f"{base_url}/scheduled_events"
                    params = {"user": user_uri, "count": 20}
                    async with session.get(url, headers=headers, params=params) as resp:
                        if resp.status != 200:
                            return {"status": "error", "error": f"Calendly Error: {resp.status}"}
                        res_data = await resp.json()
                        return {"status": "success", "data": {"result": res_data.get("collection", [])}}

                elif action == "get_event":
                    event_uuid = self.get_config("event_uuid") or str(input_data)
                    url = f"{base_url}/scheduled_events/{event_uuid}"
                    async with session.get(url, headers=headers) as resp:
                        if resp.status != 200:
                            return {"status": "error", "error": f"Calendly Error: {resp.status}"}
                        res_data = await resp.json()
                        return {"status": "success", "data": {"result": res_data.get("resource", {})}}

                elif action == "list_event_types":
                    # Get user first
                    url = f"{base_url}/users/me"
                    async with session.get(url, headers=headers) as resp:
                        if resp.status != 200:
                            return {"status": "error", "error": f"Calendly Error: {resp.status}"}
                        user_data = await resp.json()
                        user_uri = user_data.get("resource", {}).get("uri")
                    
                    url = f"{base_url}/event_types"
                    params = {"user": user_uri}
                    async with session.get(url, headers=headers, params=params) as resp:
                        if resp.status != 200:
                            return {"status": "error", "error": f"Calendly Error: {resp.status}"}
                        res_data = await resp.json()
                        return {"status": "success", "data": {"result": res_data.get("collection", [])}}

                return {"status": "error", "error": f"Unsupported action: {action}"}

        except Exception as e:
            return {"status": "error", "error": f"Calendly Node Failed: {str(e)}"}
