from ...base import BaseNode
from typing import Any, Dict, Optional
import json
import requests

from langchain.tools import BaseTool
from pydantic import Field

class ZapierTool(BaseTool):
    name: str = "zapier_connector"
    description: str = "Connect to Zapier workflows via Webhooks. Use this to trigger thousands of third-party apps."

    def _run(self, webhook_url: str, data: Dict[str, Any]) -> str:
        try:
            response = requests.post(webhook_url, json=data)
            if response.status_code == 200:
                return "Zapier: Workflow triggered successfully."
            else:
                return f"Zapier Error: Received status code {response.status_code}"
        except Exception as e:
            return f"Zapier Error: {str(e)}"

class ZapierNode(BaseNode):
    async def execute(self, input_data: Any = None, context: Optional[Dict[str, Any]] = None) -> Any:
        webhook_url = self.config.get("webhook_url")
        data = self.config.get("data", {})
        
        if not webhook_url:
            return "Error: Zapier Webhook URL is missing."
            
        tool = ZapierTool()
        return tool._run(webhook_url=webhook_url, data=data)

    async def get_langchain_object(self, context: Optional[Dict[str, Any]] = None) -> Any:
        return ZapierTool()
