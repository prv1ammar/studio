"""
Workato Node - Studio Standard (Universal Method)
Batch 101: Automation Bridges (Interoperability)
"""
from typing import Any, Dict, Optional, List
import aiohttp
from ...base import BaseNode
from ...registry import register_node

@register_node("workato_node")
class WorkatoNode(BaseNode):
    """
    Trigger Workato Recipes via Webhooks.
    """
    node_type = "workato_node"
    version = "1.0.0"
    category = "bridges"
    credentials_required = ["workato_auth"]

    inputs = {
        "webhook_url": {
             "type": "string",
             "required": True,
             "description": "Workato Webhook URL"
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
            # Usually Workato webhooks are authenticated if configured, or just open.
            # We add options for header auth if needed via credentials.
            creds = await self.get_credential("workato_auth")
            token = creds.get("api_token") # Optional Auth Token often used in header
            
            url = self.get_config("webhook_url")
            payload_str = self.get_config("payload") or str(input_data)
            
            if not url:
                 return {"status": "error", "error": "webhook_url required"}
            
            headers = {"Content-Type": "application/json"}
            if token:
                 headers["Authorization"] = f"Bearer {token}"
            
            import json
            try:
                data = json.loads(payload_str) if isinstance(payload_str, str) else payload_str
            except:
                data = {"data": payload_str}

            async with aiohttp.ClientSession() as session:
                async with session.post(url, headers=headers, json=data) as resp:
                    text = await resp.text()
                    if resp.status not in [200, 201, 202]:
                         return {"status": "error", "error": f"Workato Error: {resp.status} - {text}"}
                    
                    return {
                        "status": "success",
                        "data": {
                            "result": {"response": text}
                        }
                    }

        except Exception as e:
             return {"status": "error", "error": f"Workato Node Failed: {str(e)}"}

