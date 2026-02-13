"""
ShipStation Node - Studio Standard
Batch 65: Logistics & Shipping
"""
from typing import Any, Dict, Optional, List
import aiohttp
import base64
from ...base import BaseNode
from ...registry import register_node

@register_node("shipstation_node")
class ShipStationNode(BaseNode):
    """
    Automate e-commerce fulfillment and label generation via ShipStation.
    """
    node_type = "shipstation_node"
    version = "1.0.0"
    category = "logistics"
    credentials_required = ["shipstation_auth"]

    inputs = {
        "action": {
            "type": "dropdown",
            "default": "list_orders",
            "options": ["list_orders", "create_order", "get_order", "list_shipments", "create_label"],
            "description": "ShipStation action"
        },
        "order_id": {
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
            # 1. Resolve Auth
            creds = await self.get_credential("shipstation_auth")
            api_key = creds.get("api_key") if creds else self.get_config("api_key")
            api_secret = creds.get("api_secret") if creds else self.get_config("api_secret")
            
            if not api_key or not api_secret:
                return {"status": "error", "error": "ShipStation API Key and Secret are required."}

            auth_str = f"{api_key}:{api_secret}"
            encoded_auth = base64.b64encode(auth_str.encode()).decode()
            
            headers = {
                "Authorization": f"Basic {encoded_auth}",
                "Content-Type": "application/json"
            }
            
            base_url = "https://ssapi.shipstation.com"
            action = self.get_config("action", "list_orders")

            async with aiohttp.ClientSession() as session:
                if action == "list_orders":
                    async with session.get(f"{base_url}/orders", headers=headers) as resp:
                        res_data = await resp.json()
                        orders = res_data.get("orders", [])
                        return {"status": "success", "data": {"result": orders, "count": len(orders)}}

                elif action == "get_order":
                    oid = self.get_config("order_id") or str(input_data)
                    async with session.get(f"{base_url}/orders/{oid}", headers=headers) as resp:
                        res_data = await resp.json()
                        return {"status": "success", "data": {"result": res_data}}

                elif action == "list_shipments":
                    async with session.get(f"{base_url}/shipments", headers=headers) as resp:
                        res_data = await resp.json()
                        shipments = res_data.get("shipments", [])
                        return {"status": "success", "data": {"result": shipments, "count": len(shipments)}}

                return {"status": "error", "error": f"Unsupported action: {action}"}

        except Exception as e:
            return {"status": "error", "error": f"ShipStation Node Failed: {str(e)}"}
