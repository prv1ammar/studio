"""
Fathom Node - Studio Standard
Batch 70: Advanced Analytics
"""
from typing import Any, Dict, Optional, List
import aiohttp
from ...base import BaseNode
from ...registry import register_node

@register_node("fathom_node")
class FathomNode(BaseNode):
    """
    Privacy-first web analytics via Fathom Analytics.
    """
    node_type = "fathom_node"
    version = "1.0.0"
    category = "analytics"
    credentials_required = ["fathom_auth"]

    inputs = {
        "action": {
            "type": "dropdown",
            "default": "list_sites",
            "options": ["list_sites", "get_site", "get_aggregation"],
            "description": "Fathom action"
        },
        "site_id": {
            "type": "string",
            "optional": True
        },
        "date_from": {
            "type": "string",
            "optional": True,
            "description": "YYYY-MM-DD"
        }
    }

    outputs = {
        "result": {"type": "any"},
        "status": {"type": "string"}
    }

    async def execute(self, input_data: Any, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        try:
            creds = await self.get_credential("fathom_auth")
            api_token = creds.get("api_token") if creds else self.get_config("api_token")
            
            if not api_token:
                return {"status": "error", "error": "Fathom API Token is required."}

            headers = {
                "Authorization": f"Bearer {api_token}",
                "Accept": "application/json"
            }
            
            base_url = "https://api.usefathom.com/v1"
            action = self.get_config("action", "list_sites")

            async with aiohttp.ClientSession() as session:
                if action == "list_sites":
                    async with session.get(f"{base_url}/sites", headers=headers) as resp:
                        res_data = await resp.json()
                        data = res_data.get("data", [])
                        return {"status": "success", "data": {"result": data, "count": len(data)}}

                elif action == "get_aggregation":
                    site_id = self.get_config("site_id")
                    if not site_id:
                        return {"status": "error", "error": "site_id is required for aggregation."}
                    
                    params = {
                        "entity": "pageview",
                        "entity_id": site_id,
                        "aggregates": "visits,uniques,pageviews",
                        "date_from": self.get_config("date_from", "2024-01-01")
                    }
                    async with session.get(f"{base_url}/aggregations", headers=headers, params=params) as resp:
                        res_data = await resp.json()
                        return {"status": "success", "data": {"result": res_data}}

                return {"status": "error", "error": f"Unsupported action: {action}"}

        except Exception as e:
            return {"status": "error", "error": f"Fathom Node Failed: {str(e)}"}
