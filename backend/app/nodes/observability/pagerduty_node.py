"""
PagerDuty Node - Studio Standard
Batch 83: Observability & SRE
"""
from typing import Any, Dict, Optional, List
import aiohttp
from ...base import BaseNode
from ...registry import register_node

@register_node("pagerduty_node")
class PagerDutyNode(BaseNode):
    """
    Manage incidents, on-calls, and escalations via PagerDuty API v2.
    """
    node_type = "pagerduty_node"
    version = "1.0.0"
    category = "observability"
    credentials_required = ["pagerduty_auth"]

    inputs = {
        "action": {
            "type": "dropdown",
            "default": "list_incidents",
            "options": ["list_incidents", "get_incident", "create_incident", "list_oncalls", "list_services"],
            "description": "PagerDuty action"
        },
        "incident_id": {
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
            creds = await self.get_credential("pagerduty_auth")
            api_token = creds.get("api_token") if creds else self.get_config("api_token")
            
            if not api_token:
                return {"status": "error", "error": "PagerDuty API Token ISO required."}

            headers = {
                "Authorization": f"Token token={api_token}",
                "Accept": "application/vnd.pagerduty+json;version=2",
                "Content-Type": "application/json"
            }
            
            base_url = "https://api.pagerduty.com"
            action = self.get_config("action", "list_incidents")

            async with aiohttp.ClientSession() as session:
                if action == "list_incidents":
                    url = f"{base_url}/incidents"
                    async with session.get(url, headers=headers) as resp:
                        res_data = await resp.json()
                        return {"status": "success", "data": {"result": res_data.get("incidents", [])}}

                elif action == "list_oncalls":
                    url = f"{base_url}/oncalls"
                    async with session.get(url, headers=headers) as resp:
                        res_data = await resp.json()
                        return {"status": "success", "data": {"result": res_data.get("oncalls", [])}}

                return {"status": "error", "error": f"Unsupported action: {action}"}

        except Exception as e:
            return {"status": "error", "error": f"PagerDuty Node Failed: {str(e)}"}
