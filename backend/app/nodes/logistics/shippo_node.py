"""
Shippo Node - Studio Standard
Batch 65: Logistics & Shipping
"""
from typing import Any, Dict, Optional, List
import aiohttp
from ...base import BaseNode
from ...registry import register_node

@register_node("shippo_node")
class ShippoNode(BaseNode):
    """
    Compare shipping rates and create labels via Shippo.
    """
    node_type = "shippo_node"
    version = "1.0.0"
    category = "logistics"
    credentials_required = ["shippo_auth"]

    inputs = {
        "action": {
            "type": "dropdown",
            "default": "list_shipments",
            "options": ["list_shipments", "create_shipment", "get_rates", "create_label"],
            "description": "Shippo action"
        }
    }

    outputs = {
        "result": {"type": "any"},
        "status": {"type": "string"},
        "count": {"type": "number"}
    }

    async def execute(self, input_data: Any, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        try:
            creds = await self.get_credential("shippo_auth")
            api_token = creds.get("api_token") if creds else self.get_config("api_token")
            
            if not api_token:
                return {"status": "error", "error": "Shippo API Token is required."}

            headers = {
                "Authorization": f"ShippoToken {api_token}",
                "Content-Type": "application/json"
            }
            
            base_url = "https://api.goshippo.com"
            action = self.get_config("action", "list_shipments")

            async with aiohttp.ClientSession() as session:
                if action == "list_shipments":
                    async with session.get(f"{base_url}/shipments/", headers=headers) as resp:
                        res_data = await resp.json()
                        results = res_data.get("results", [])
                        return {"status": "success", "data": {"result": results, "count": len(results)}}
                
                return {"status": "error", "error": f"Unsupported action: {action}"}

        except Exception as e:
            return {"status": "error", "error": f"Shippo Node Failed: {str(e)}"}
