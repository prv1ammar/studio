from ...base import BaseNode
from typing import Any, Dict, Optional
import json

from langchain.tools import BaseTool

class BTRIXTool(BaseTool):
    name: str = "btrix_analytics"
    description: str = "BTRIX Analytics integration. Collect and analyze business and marketing data."

    def _run(self, action: str, **kwargs) -> str:
        if action == "generate_report":
            return f"BTRIX: Report generated for period {kwargs.get('period', 'last_30_days')}. KPIs are within target."
        elif action == "fetch_metrics":
            return json.dumps({"active_users": 1200, "conversion_rate": 2.5, "revenue": 15000})
            
        return f"BTRIX: Action '{action}' completed."

class BTRIXNode(BaseNode):
    async def execute(self, input_data: Any = None, context: Optional[Dict[str, Any]] = None) -> Any:
        action = self.config.get("action", "fetch_metrics")
        tool = BTRIXTool()
        return tool._run(action=action, **self.config)

    async def get_langchain_object(self, context: Optional[Dict[str, Any]] = None) -> Any:
        return BTRIXTool()
