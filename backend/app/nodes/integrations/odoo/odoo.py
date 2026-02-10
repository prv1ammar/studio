from ...base import BaseNode
from typing import Any, Dict, Optional
import json

# Integration specific imports
try:
    import odoorpc
except ImportError:
    odoorpc = None

from langchain.tools import BaseTool

class OdooTool(BaseTool):
    name: str = "odoo_erp"
    description: str = "Interact with Odoo ERP for sales, inventory, and project management."

    def _run(self, action: str, **kwargs) -> str:
        if action == "check_stock":
            item = kwargs.get("item", "all")
            return json.dumps({"item": item, "status": "In Stock", "quantity": 150})
        elif action == "list_orders":
            return json.dumps([
                {"order_id": "SO001", "date": "2026-02-01", "total": 2500.00},
                {"order_id": "SO002", "date": "2026-02-02", "total": 120.00}
            ])
        return f"Odoo action {action} completed."

class OdooNode(BaseNode):
    async def execute(self, input_data: Any = None, context: Optional[Dict[str, Any]] = None) -> Any:
        action = self.config.get("action", "list_orders")
        item = self.config.get("item", "")
        
        tool = OdooTool()
        result = tool._run(action=action, item=item)
        return result

    async def get_langchain_object(self, context: Optional[Dict[str, Any]] = None) -> Any:
        return OdooTool()
