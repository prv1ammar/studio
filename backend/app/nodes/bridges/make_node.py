"""
Make (Integromat) Node - Studio Standard (Universal Method)
Batch 101: Automation Bridges (Interoperability)
"""
from typing import Any, Dict, Optional, List
import aiohttp
from ...base import BaseNode
from ...registry import register_node

@register_node("make_node")
class MakeNode(BaseNode):
    """
    Trigger Make.com (formerly Integromat) Scenarios via Webhook.
    """
    node_type = "make_node"
    version = "1.0.0"
    category = "bridges"
    credentials_required = [] # Often just a webhook URL, or auth header if protected

    inputs = {
        "webhook_url": {
            "type": "string",
            "required": True,
            "description": "Make Custom Webhook URL"
        },
        "payload": {
            "type": "string",
            "required": True,
            "description": "JSON payload to send"
        }
    }

    outputs = {
        "result": {"type": "any"},
        "status": {"type": "string"}
    }

    async def execute(self, input_data: Any, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        try:
            webhook_url = self.get_config("webhook_url")
            payload_str = self.get_config("payload") or str(input_data)
            
            if not webhook_url:
                return {"status": "error", "error": "webhook_url required"}
            
            import json
            try:
                data = json.loads(payload_str) if isinstance(payload_str, str) else payload_str
            except:
                data = {"data": payload_str} # Fallback wrapper
            
            headers = {"Content-Type": "application/json"}
            
            async with aiohttp.ClientSession() as session:
                async with session.post(webhook_url, headers=headers, json=data) as resp:
                    # Make webhooks return 200 "Accepted" usually
                    text = await resp.text()
                    
                    if resp.status not in [200, 201, 202]:
                         return {"status": "error", "error": f"Make.com Webhook Error: {resp.status} - {text}"}
                    
                    return {
                        "status": "success",
                        "data": {
                            "result": {"response": text, "status": resp.status}
                        }
                    }

        except Exception as e:
            return {"status": "error", "error": f"Make Node Failed: {str(e)}"}
