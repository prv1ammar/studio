from typing import Any, Dict, Optional
from ..base import BaseNode
from ..registry import register_node
import json

@register_node("webhook_trigger")
class WebhookTriggerNode(BaseNode):
    """
    Standardized Webhook Trigger Node.
    Serves as the entry point for external HTTP callbacks.
    """
    node_type = "webhook_trigger"
    version = "1.0.0"
    category = "trigger"
    

    properties = [
        {
            'displayName': 'Expected Auth Header',
            'name': 'expected_auth_header',
            'type': 'string',
            'default': '',
            'description': 'Optional API Key to expect in headers',
        },
        {
            'displayName': 'Method',
            'name': 'method',
            'type': 'string',
            'default': 'POST',
        },
        {
            'displayName': 'Path',
            'name': 'path',
            'type': 'string',
            'default': '',
            'description': 'Custom sub-path (optional)',
        },
    ]
    inputs = {
        "method": {"type": "string", "default": "POST", "enum": ["GET", "POST"]},
        "expected_auth_header": {"type": "string", "description": "Optional API Key to expect in headers"},
        "path": {"type": "string", "description": "Custom sub-path (optional)"}
    }
    
    outputs = {
        "payload": {"type": "object", "description": "The received JSON body or query params"},
        "headers": {"type": "object", "description": "HTTP headers received"},
        "status": {"type": "string"}
    }
    
    credentials_required = []

    async def execute(self, input_data: Any, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        In most cases, the webhook trigger receives data from the engine entry point.
        However, if executed manually, it validates the structure of input_data.
        """
        try:
            # Check context for raw request info if available
            request_info = context.get("http_request", {}) if context else {}
            
            # Use input_data if it came from the engine seed
            payload = input_data if input_data else request_info.get("body", {})
            
            # 1. Method Validation
            allowed_method = self.get_config("method", "POST").upper()
            request_method = request_info.get("method", "POST").upper()
            
            if request_method != allowed_method and request_info:
                return {
                    "status": "error", 
                    "error": f"Invalid method: expected {allowed_method}, got {request_method}"
                }
            
            # 2. Payload Parsing (Ensure it's a dict if JSON)
            if isinstance(payload, str):
                try:
                    payload = json.loads(payload)
                except:
                    payload = {"raw_text": payload}
            
            return {
                "status": "success",
                "data": {
                    "payload": payload,
                    "headers": request_info.get("headers", {}),
                    "method": request_method
                }
            }
            
        except Exception as e:
            return {"status": "error", "error": f"Webhook processing failed: {str(e)}"}