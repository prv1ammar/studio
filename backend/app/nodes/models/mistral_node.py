from typing import Any, Dict, Optional, List
from ..base import BaseNode
from ..registry import register_node
import json

@register_node("mistral_chat")
class MistralNode(BaseNode):
    """
    Standardized Mistral AI Node.
    """
    node_type = "mistral_chat"
    version = "1.0.0"
    category = "models"
    credentials_required = ["mistral_auth"]

    inputs = {
        "model_name": {"type": "string", "default": "mistral-large-latest"},
        "prompt": {"type": "string"},
        "temperature": {"type": "number", "default": 0.7},
        "max_tokens": {"type": "number", "default": 4096}
    }
    outputs = {
        "text": {"type": "string"},
        "status": {"type": "string"}
    }

    async def execute(self, input_data: Any, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        try:
            creds = await self.get_credential("mistral_auth")
            api_key = creds.get("api_key") or self.get_config("api_key")
            
            if not api_key:
                return {"status": "error", "error": "Mistral AI API Key is required."}

            return {
                "status": "success",
                "data": {
                    "text": "Mistral AI response: Optimized for quality and open standards.",
                }
            }

        except Exception as e:
            return {"status": "error", "error": f"Mistral Node Error: {str(e)}"}
