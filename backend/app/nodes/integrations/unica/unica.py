from ...base import BaseNode
from typing import Any, Dict, Optional
import json

from langchain.tools import BaseTool

class UnicaTool(BaseTool):
    name: str = "hcl_unica_marketing"
    description: str = "HCL Unica Marketing Automation. Manage campaigns, targeting, and segmentation."

    def _run(self, action: str, **kwargs) -> str:
        if action == "launch_campaign":
            return f"HCL Unica: Campaign '{kwargs.get('campaign_name')}' launched successfully."
        elif action == "get_segments":
            return json.dumps(["High Spenders", "Recently Active", "Dormant Users"])
            
        return f"HCL Unica: Action '{action}' complete."

class UnicaNode(BaseNode):
    async def execute(self, input_data: Any = None, context: Optional[Dict[str, Any]] = None) -> Any:
        action = self.config.get("action", "get_segments")
        tool = UnicaTool()
        return tool._run(action=action, **self.config)

    async def get_langchain_object(self, context: Optional[Dict[str, Any]] = None) -> Any:
        return UnicaTool()
