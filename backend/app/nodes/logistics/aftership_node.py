"""
AfterShip Node - Studio Standard
Batch 65: Logistics & Shipping
"""
from typing import Any, Dict, Optional, List
import aiohttp
from ..base import BaseNode
from ..registry import register_node

@register_node("aftership_node")
class AfterShipNode(BaseNode):
    """
    Track shipments and manage notifications via AfterShip.
    """
    node_type = "aftership_node"
    version = "1.0.0"
    category = "logistics"
    credentials_required = ["aftership_auth"]


    properties = [
        {
            'displayName': 'Operation',
            'name': 'operation',
            'type': 'options',
            'default': 'list_trackings',
            'options': [
                {'name': 'List Trackings', 'value': 'list_trackings'},
                {'name': 'Create Tracking', 'value': 'create_tracking'},
                {'name': 'Get Tracking', 'value': 'get_tracking'},
                {'name': 'List Couriers', 'value': 'list_couriers'},
            ],
            'description': 'AfterShip action',
        },
        {
            'displayName': 'Slug',
            'name': 'slug',
            'type': 'string',
            'default': '',
            'description': 'Courier slug (e.g. 'fedex', 'ups')',
        },
        {
            'displayName': 'Tracking Number',
            'name': 'tracking_number',
            'type': 'string',
            'default': '',
        },
    ]
    inputs = {
        "action": {
            "type": "dropdown",
            "default": "list_trackings",
            "options": ["list_trackings", "create_tracking", "get_tracking", "list_couriers"],
            "description": "AfterShip action"
        },
        "tracking_number": {
            "type": "string",
            "optional": True
        },
        "slug": {
            "type": "string",
            "optional": True,
            "description": "Courier slug (e.g. 'fedex', 'ups')"
        }
    }

    outputs = {
        "result": {"type": "any"},
        "status": {"type": "string"},
        "count": {"type": "number"}
    }

    async def execute(self, input_data: Any, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        try:
            creds = await self.get_credential("aftership_auth")
            api_key = creds.get("api_key") if creds else self.get_config("api_key")
            
            if not api_key:
                return {"status": "error", "error": "AfterShip API Key is required."}

            headers = {
                "aftership-api-key": api_key,
                "Content-Type": "application/json"
            }
            
            base_url = "https://api.aftership.com/v4"
            action = self.get_config("action", "list_trackings")

            async with aiohttp.ClientSession() as session:
                if action == "list_trackings":
                    async with session.get(f"{base_url}/trackings", headers=headers) as resp:
                        res_data = await resp.json()
                        trackings = res_data.get("data", {}).get("trackings", [])
                        return {"status": "success", "data": {"result": trackings, "count": len(trackings)}}

                elif action == "get_tracking":
                    slug = self.get_config("slug")
                    tracking_number = self.get_config("tracking_number") or str(input_data)
                    url = f"{base_url}/trackings/{slug}/{tracking_number}"
                    async with session.get(url, headers=headers) as resp:
                        res_data = await resp.json()
                        return {"status": "success", "data": {"result": res_data.get("data")}}

                elif action == "list_couriers":
                    async with session.get(f"{base_url}/couriers", headers=headers) as resp:
                        res_data = await resp.json()
                        couriers = res_data.get("data", {}).get("couriers", [])
                        return {"status": "success", "data": {"result": couriers, "count": len(couriers)}}
                
                return {"status": "error", "error": f"Unsupported action: {action}"}

        except Exception as e:
            return {"status": "error", "error": f"AfterShip Node Failed: {str(e)}"}