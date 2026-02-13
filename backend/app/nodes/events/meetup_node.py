"""
Meetup Node - Studio Standard
Batch 68: Event Management
"""
from typing import Any, Dict, Optional, List
import aiohttp
from ...base import BaseNode
from ...registry import register_node

@register_node("meetup_node")
class MeetupNode(BaseNode):
    """
    Automate local group discovery and RSVP management via Meetup GraphQL API.
    """
    node_type = "meetup_node"
    version = "1.0.0"
    category = "events"
    credentials_required = ["meetup_auth"]

    inputs = {
        "action": {
            "type": "dropdown",
            "default": "get_self",
            "options": ["get_self", "list_groups", "search_events"],
            "description": "Meetup action"
        },
        "query": {
            "type": "string",
            "optional": True,
            "description": "Search query for groups or events"
        }
    }

    outputs = {
        "result": {"type": "any"},
        "status": {"type": "string"}
    }

    async def execute(self, input_data: Any, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        try:
            creds = await self.get_credential("meetup_auth")
            access_token = creds.get("access_token") if creds else self.get_config("access_token")
            
            if not access_token:
                return {"status": "error", "error": "Meetup OAuth Access Token is required."}

            headers = {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json"
            }
            
            base_url = "https://api.meetup.com/gql"
            action = self.get_config("action", "get_self")

            async with aiohttp.ClientSession() as session:
                if action == "get_self":
                    query = """
                    query {
                      self {
                        id
                        name
                        email
                      }
                    }
                    """
                    async with session.post(base_url, headers=headers, json={"query": query}) as resp:
                        res_data = await resp.json()
                        return {"status": "success", "data": {"result": res_data.get("data", {}).get("self")}}

                elif action == "list_groups":
                    query = """
                    query {
                      self {
                        memberships {
                          edges {
                            node {
                              id
                              name
                              urlname
                            }
                          }
                        }
                      }
                    }
                    """
                    async with session.post(base_url, headers=headers, json={"query": query}) as resp:
                        res_data = await resp.json()
                        memberships = res_data.get("data", {}).get("self", {}).get("memberships", {}).get("edges", [])
                        return {"status": "success", "data": {"result": [m["node"] for m in memberships]}}

                return {"status": "error", "error": f"Unsupported Meetup action: {action}"}

        except Exception as e:
            return {"status": "error", "error": f"Meetup Node Failed: {str(e)}"}
