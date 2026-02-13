"""
Power Automate Node - Studio Standard (Universal Method)
Batch 101: Automation Bridges (Interoperability)
"""
from typing import Any, Dict, Optional, List
import aiohttp
from ...base import BaseNode
from ...registry import register_node

@register_node("power_automate_node")
class PowerAutomateNode(BaseNode):
    """
    Trigger Microsoft Power Automate (Flow) via HTTP Trigger.
    """
    node_type = "power_automate_node"
    version = "1.0.0"
    category = "bridges"
    credentials_required = [] # URL usually contains the SAS token

    inputs = {
        "webhook_url": {
            "type": "string",
            "required": True,
            "description": "The HTTP POST URL from Power Automate Flow"
        },
        "payload": {
            "type": "string",
            "required": True,
            "description": "JSON payload"
        }
    }

    outputs = {
        "result": {"type": "any"},
        "status": {"type": "string"}
    }

    async def execute(self, input_data: Any, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        try:
            url = self.get_config("webhook_url")
            payload_str = self.get_config("payload") or str(input_data)
            
            if not url:
                return {"status": "error", "error": "webhook_url required"}

            import json
            try:
                data = json.loads(payload_str) if isinstance(payload_str, str) else payload_str
            except:
                data = {"content": payload_str}

            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=data) as resp:
                    text = await resp.text()
                    if resp.status not in [200, 201, 202]:
                         return {"status": "error", "error": f"Power Automate Error: {resp.status} - {text}"}
                    
                    return {
                        "status": "success",
                        "data": {
                            "result": {"message": "Flow Triggered"}
                        }
                    }

        except Exception as e:
            return {"status": "error", "error": f"Power Automate Node Failed: {str(e)}"}
