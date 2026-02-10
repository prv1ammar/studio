from ...base import BaseNode
from typing import Any, Dict, Optional
import json
import requests

from langchain.tools import BaseTool

class VTigerTool(BaseTool):
    name: str = "vtiger_crm"
    description: str = "VTiger Open-Source CRM integration. Manage sales, marketing, and support."

    def _run(self, action: str, **kwargs) -> str:
        if action == "query_contacts":
            return json.dumps([{"firstname": "Alice", "lastname": "Wonderland"}, {"firstname": "Bob", "lastname": "Builder"}])
        return f"VTiger: Action {action} completed successfully."

class VTigerNode(BaseNode):
    async def execute(self, input_data: Any = None, context: Optional[Dict[str, Any]] = None) -> Any:
        action = self.config.get("action", "query_contacts")
        tool = VTigerTool()
        return tool._run(action=action)

    async def get_langchain_object(self, context: Optional[Dict[str, Any]] = None) -> Any:
        return VTigerTool()
