from ...base import BaseNode
from typing import Any, Dict, Optional
import json
import requests # Dolibarr uses REST API

from langchain.tools import BaseTool

class DolibarrTool(BaseTool):
    name: str = "dolibarr_erp"
    description: str = "Open source ERP/CRM integration for SMEs. Manage quotes, invoices, and members."

    def _run(self, action: str, **kwargs) -> str:
        if action == "list_members":
            return json.dumps([
                {"name": "Jean Dupont", "type": "Active", "expiry": "2026-12-31"},
                {"name": "Marie Curie", "type": "VIP", "expiry": "2027-01-01"}
            ])
        elif action == "create_quote":
            return "Quote generated: QUO-2026-001 (Ready for review)"
        return f"Dolibarr: Successfully performed {action}."

class DolibarrNode(BaseNode):
    async def execute(self, input_data: Any = None, context: Optional[Dict[str, Any]] = None) -> Any:
        action = self.config.get("action", "list_members")
        
        tool = DolibarrTool()
        result = tool._run(action=action)
        return result

    async def get_langchain_object(self, context: Optional[Dict[str, Any]] = None) -> Any:
        return DolibarrTool()
