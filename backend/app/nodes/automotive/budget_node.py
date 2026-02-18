"""
Budget Node - Studio Standard (Universal Method)
Batch 88: Automotive & Fleet
"""
from typing import Any, Dict, Optional, List
import aiohttp
from ..base import BaseNode
from...registry import register_node

@register_node("budget_node")
class BudgetNode(BaseNode):
    """
    Manage Budget discount rental fleet logistics and reservations.
    """
    node_type = "budget_node"
    version = "1.0.0"
    category = "automotive"
    credentials_required = ["budget_auth"]


    properties = [
        {
            'displayName': 'Operation',
            'name': 'operation',
            'type': 'options',
            'default': 'search_vehicles',
            'options': [
                {'name': 'Search Vehicles', 'value': 'search_vehicles'},
                {'name': 'Get Rates', 'value': 'get_rates'},
                {'name': 'Create Booking', 'value': 'create_booking'},
            ],
            'description': 'Budget action',
        },
        {
            'displayName': 'Location Code',
            'name': 'location_code',
            'type': 'string',
            'default': '',
        },
    ]
    inputs = {
        "action": {
            "type": "dropdown",
            "default": "search_vehicles",
            "options": ["search_vehicles", "get_rates", "create_booking"],
            "description": "Budget action"
        },
        "location_code": {
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
            creds = await self.get_credential("budget_auth")
            api_key = creds.get("api_key")
            
            if not api_key:
                return {"status": "error", "error": "Budget API Key required."}

            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            }
            
            # 2. Connect to Real API
            base_url = "https://stage.abgapiservices.com:443/cars/catalog/v1"
            action = self.get_config("action", "search_vehicles")

            async with aiohttp.ClientSession() as session:
                if action == "search_vehicles":
                    loc = self.get_config("location_code") or str(input_data)
                    url = f"{base_url}/vehicles"
                    params = {"brand": "Budget", "pickUpLocation": loc}
                    async with session.get(url, headers=headers, params=params) as resp:
                        if resp.status != 200:
                            return {"status": "error", "error": f"Budget API Error: {resp.status}"}
                        res_data = await resp.json()
                        return {"status": "success", "data": {"result": res_data.get("vehicles", [])}}

                return {"status": "error", "error": f"Unsupported action: {action}"}

        except Exception as e:
            return {"status": "error", "error": f"Budget Node Failed: {str(e)}"}