"""
Eventbrite Node - Studio Standard
Batch 68: Event Management
"""
from typing import Any, Dict, Optional, List
import aiohttp
from ...base import BaseNode
from ...registry import register_node

@register_node("eventbrite_node")
class EventbriteNode(BaseNode):
    """
    Automate event discovery and ticket management via Eventbrite API v3.
    """
    node_type = "eventbrite_node"
    version = "1.0.0"
    category = "events"
    credentials_required = ["eventbrite_auth"]

    inputs = {
        "action": {
            "type": "dropdown",
            "default": "list_events",
            "options": ["list_events", "get_event", "list_organizations", "search_events"],
            "description": "Eventbrite action"
        },
        "organization_id": {
            "type": "string",
            "optional": True,
            "description": "Unique ID of the organization"
        },
        "event_id": {
            "type": "string",
            "optional": True
        }
    }

    outputs = {
        "result": {"type": "any"},
        "status": {"type": "string"},
        "count": {"type": "number"}
    }

    async def execute(self, input_data: Any, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        try:
            creds = await self.get_credential("eventbrite_auth")
            api_token = creds.get("api_token") if creds else self.get_config("api_token")
            
            if not api_token:
                return {"status": "error", "error": "Eventbrite Private Token is required."}

            headers = {
                "Authorization": f"Bearer {api_token}",
                "Accept": "application/json"
            }
            
            base_url = "https://www.eventbriteapi.com/v3"
            action = self.get_config("action", "list_events")

            async with aiohttp.ClientSession() as session:
                if action == "list_organizations":
                    url = f"{base_url}/users/me/organizations/"
                    async with session.get(url, headers=headers) as resp:
                        res_data = await resp.json()
                        orgs = res_data.get("organizations", [])
                        return {"status": "success", "data": {"result": orgs, "count": len(orgs)}}

                elif action == "list_events":
                    org_id = self.get_config("organization_id")
                    if not org_id:
                        # Fallback: get first org if not provided? Or list user events.
                        url = f"{base_url}/users/me/events/"
                    else:
                        url = f"{base_url}/organizations/{org_id}/events/"
                    
                    async with session.get(url, headers=headers) as resp:
                        res_data = await resp.json()
                        events = res_data.get("events", [])
                        return {"status": "success", "data": {"result": events, "count": len(events)}}

                elif action == "get_event":
                    e_id = self.get_config("event_id") or str(input_data)
                    url = f"{base_url}/events/{e_id}/"
                    async with session.get(url, headers=headers) as resp:
                        res_data = await resp.json()
                        return {"status": "success", "data": {"result": res_data}}

                return {"status": "error", "error": f"Unsupported Eventbrite action: {action}"}

        except Exception as e:
            return {"status": "error", "error": f"Eventbrite Node Failed: {str(e)}"}
