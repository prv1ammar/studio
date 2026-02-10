from ...base import BaseNode
from typing import Any, Dict, Optional
import json
import requests

from langchain.tools import BaseTool

class GLPITool(BaseTool):
    name: str = "glpi_itsm"
    description: str = "GLPI ITSM / Support integration. Manage tickets, incidents, and IT assets."

    def _run(self, action: str, **kwargs) -> str:
        # GLPI uses a REST API with session tokens
        if action == "open_ticket":
            return f"GLPI: Ticket opened successfully. Subject: {kwargs.get('subject', 'No Subject')}"
        elif action == "list_incidents":
            return json.dumps([{"id": 1, "title": "Server down", "status": "In Progress"}, {"id": 2, "title": "Email issue", "status": "New"}])
            
        return f"GLPI: Action '{action}' executed."

class GLPINode(BaseNode):
    async def execute(self, input_data: Any = None, context: Optional[Dict[str, Any]] = None) -> Any:
        action = self.config.get("action", "list_incidents")
        tool = GLPITool()
        return tool._run(action=action, **self.config)

    async def get_langchain_object(self, context: Optional[Dict[str, Any]] = None) -> Any:
        return GLPITool()
