"""
Webhook Response Node - Studio Standard (Universal Method)
Batch 99: Web & Utilities (Deepening Parity)
"""
from typing import Any, Dict, Optional, List
from ..base import BaseNode
from ..registry import register_node

@register_node("webhook_response_node")
class WebhookResponseNode(BaseNode):
    """
    Send a response to the Webhook that triggered the workflow.
    """
    node_type = "webhook_response_node"
    version = "1.0.0"
    category = "utilities"
    credentials_required = []


    properties = [
        {
            'displayName': 'Response Body',
            'name': 'response_body',
            'type': 'string',
            'default': '',
            'description': 'JSON Body',
        },
        {
            'displayName': 'Response Code',
            'name': 'response_code',
            'type': 'string',
            'default': 200,
            'description': 'HTTP Status Code',
        },
        {
            'displayName': 'Response Headers',
            'name': 'response_headers',
            'type': 'string',
            'default': '',
            'description': 'JSON Headers',
        },
    ]
    inputs = {
        "response_code": {
            "type": "number",
            "default": 200,
            "description": "HTTP Status Code"
        },
        "response_body": {
            "type": "string",
            "optional": True,
            "description": "JSON Body"
        },
        "response_headers": {
            "type": "string",
            "optional": True,
            "description": "JSON Headers"
        }
    }

    outputs = {
        "status": {"type": "string"}
    }

    async def execute(self, input_data: Any, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        try:
            # Logic: In a real engine, this would set a flag or object in the context
            # that the engine reads to send the response back.
            # Assuming context has a 'webhook_response' key or similar mechanism.
            
            code = int(self.get_config("response_code", 200))
            body = self.get_config("response_body") or str(input_data)
            headers = self.get_config("response_headers", "{}")
            
            import json
            headers_dict = json.loads(headers) if isinstance(headers, str) else headers
            
            # Simple placeholder logic for now
            # In production, context.set_webhook_response(code, body, headers)
            
            return {
                "status": "success",
                "data": {
                    "webhook_response": {
                        "status_code": code,
                        "body": body,
                        "headers": headers_dict
                    }
                }
            }

        except Exception as e:
            return {"status": "error", "error": f"Webhook Response failed: {str(e)}"}