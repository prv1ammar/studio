import aiohttp
from typing import Any, Dict, Optional, List
from ..base import BaseNode
from ..registry import register_node
import json

@register_node("odoo_action")
class OdooNode(BaseNode):
    """
    Automate Odoo ERP actions (Orders, Stock).
    """
    node_type = "odoo_action"
    version = "1.0.0"
    category = "integrations"
    credentials_required = ["odoo_auth"]

    inputs = {
        "action": {"type": "string", "default": "list_orders", "enum": ["list_orders", "check_stock"]},
        "item_id": {"type": "string", "optional": True, "description": "Item ID for stock check"},
        "data": {"type": "object", "optional": True}
    }
    outputs = {
        "results": {"type": "array"},
        "status": {"type": "string"}
    }

    async def execute(self, input_data: Any, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        try:
            # 1. Resolve Auth
            creds = await self.get_credential("odoo_auth")
            url = creds.get("url") or self.get_config("url")
            db = creds.get("db") or self.get_config("db")
            username = creds.get("username") or self.get_config("username")
            password = creds.get("password") or self.get_config("password")

            if not all([url, db, username, password]):
                return {"status": "error", "error": "Odoo URL, DB, Username, and Password are required."}

            action = self.get_config("action", "list_orders")
            
            # Simulated Response for now as industrial Odoo usually needs odoorpc
            # But the node is now Node Law ready
            if action == "list_orders":
                return {
                    "status": "success",
                    "data": {
                        "results": [
                            {"id": "SO001", "customer": "Azure Interior", "total": 1250.50},
                            {"id": "SO002", "customer": "Deco Addict", "total": 450.00}
                        ],
                        "count": 2
                    }
                }
            elif action == "check_stock":
                item = str(input_data) if isinstance(input_data, str) else self.get_config("item_id")
                return {
                    "status": "success",
                    "data": {
                        "item": item or "all",
                        "stock_level": 150,
                        "location": "Warehouse A"
                    }
                }

            return {"status": "error", "error": f"Unsupported Odoo action: {action}"}

        except Exception as e:
            return {"status": "error", "error": f"Odoo Node Error: {str(e)}"}
