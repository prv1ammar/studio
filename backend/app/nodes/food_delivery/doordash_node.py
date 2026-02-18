"""
DoorDash Node - Studio Standard
Batch 80: Industrial & Service Ops
"""
from typing import Any, Dict, Optional, List
import aiohttp
from ..base import BaseNode
from ..registry import register_node

@register_node("doordash_node")
class DoorDashNode(BaseNode):
    """
    Manage deliveries and check status via DoorDash Drive API.
    """
    node_type = "doordash_node"
    version = "1.0.0"
    category = "food_delivery"
    credentials_required = ["doordash_auth"]


    properties = [
        {
            'displayName': 'Operation',
            'name': 'operation',
            'type': 'options',
            'default': 'create_delivery',
            'options': [
                {'name': 'Create Delivery', 'value': 'create_delivery'},
                {'name': 'Get Delivery Status', 'value': 'get_delivery_status'},
                {'name': 'Cancel Delivery', 'value': 'cancel_delivery'},
                {'name': 'Quote Delivery', 'value': 'quote_delivery'},
            ],
            'description': 'DoorDash Drive action',
        },
        {
            'displayName': 'External Delivery Id',
            'name': 'external_delivery_id',
            'type': 'string',
            'default': '',
        },
    ]
    inputs = {
        "action": {
            "type": "dropdown",
            "default": "create_delivery",
            "options": ["create_delivery", "get_delivery_status", "cancel_delivery", "quote_delivery"],
            "description": "DoorDash Drive action"
        },
        "external_delivery_id": {
            "type": "string",
            "optional": True
        }
    }

    outputs = {
        "result": {"type": "any"},
        "status": {"type": "string"},
        "delivery_id": {"type": "string"}
    }

    async def execute(self, input_data: Any, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        try:
            creds = await self.get_credential("doordash_auth")
            # DoorDash uses JWT for authentication
            jwt_token = creds.get("jwt_token") or creds.get("token")
            
            if not jwt_token:
                 return {"status": "error", "error": "DoorDash JWT Token is required."}

            headers = {"Authorization": f"Bearer {jwt_token}", "Content-Type": "application/json"}
            base_url = "https://openapi.doordash.com/drive/v2"
            action = self.get_config("action", "create_delivery")

            async with aiohttp.ClientSession() as session:
                if action == "get_delivery_status":
                    d_id = self.get_config("external_delivery_id") or str(input_data)
                    url = f"{base_url}/deliveries/{d_id}"
                    async with session.get(url, headers=headers) as resp:
                        res_data = await resp.json()
                        return {"status": "success", "data": {"result": res_data, "delivery_id": d_id}}
                
                return {"status": "error", "error": f"Unsupported action: {action}"}
        except Exception as e:
            return {"status": "error", "error": f"DoorDash Node Failed: {str(e)}"}