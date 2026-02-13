"""
Base64 Utility Node - Studio Standard
Batch 51: Security & Utilities
"""
import base64
from typing import Any, Dict, Optional
from ...base import BaseNode
from ...registry import register_node

@register_node("base64_node")
class Base64Node(BaseNode):
    """
    Encode or Decode strings using Base64.
    """
    node_type = "base64_node"
    version = "1.0.0"
    category = "security"

    inputs = {
        "action": {
            "type": "dropdown",
            "default": "encode",
            "options": ["encode", "decode"],
            "description": "Base64 operation"
        },
        "text": {
            "type": "string",
            "required": True,
            "description": "Text to process"
        }
    }

    outputs = {
        "result": {"type": "string"},
        "status": {"type": "string"}
    }

    async def execute(self, input_data: Any, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        try:
            action = self.get_config("action", "encode")
            text = self.get_config("text")

            # Dynamic Override
            if isinstance(input_data, str) and input_data:
                text = input_data

            if not text:
                return {"status": "error", "error": "Input text is required."}

            if action == "encode":
                encoded = base64.b64encode(text.encode('utf-8')).decode('utf-8')
                result = encoded
            elif action == "decode":
                decoded = base64.b64decode(text.encode('utf-8')).decode('utf-8')
                result = decoded
            else:
                 return {"status": "error", "error": f"Unknown action: {action}"}

            return {
                "status": "success",
                "data": {
                    "result": result,
                    "action": action,
                    "status": "processed"
                }
            }

        except Exception as e:
            return {"status": "error", "error": f"Base64 {action} failed: {str(e)}"}
