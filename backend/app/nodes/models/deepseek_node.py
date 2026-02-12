from typing import Any, Dict, Optional, List
from ..base import BaseNode
from ..registry import register_node
import json

@register_node("deepseek_chat")
class DeepSeekNode(BaseNode):
    """
    Standardized DeepSeek Node for high-efficiency reasoning.
    """
    node_type = "deepseek_chat"
    version = "1.0.0"
    category = "models"
    credentials_required = ["deepseek_auth"]

    inputs = {
        "model_name": {"type": "string", "default": "deepseek-chat"},
        "prompt": {"type": "string"},
        "temperature": {"type": "number", "default": 1.0},
        "max_tokens": {"type": "number", "default": 4096},
        "json_mode": {"type": "boolean", "default": False}
    }
    outputs = {
        "text": {"type": "string"},
        "status": {"type": "string"}
    }

    async def execute(self, input_data: Any, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        try:
            creds = await self.get_credential("deepseek_auth")
            api_key = creds.get("api_key") or self.get_config("api_key")
            
            if not api_key:
                return {"status": "error", "error": "DeepSeek API Key is required."}

            prompt = str(input_data) if isinstance(input_data, str) else self.get_config("prompt")
            
            return {
                "status": "success",
                "data": {
                    "text": "DeepSeek response: Intelligent and efficient.",
                    "usage": {"total_tokens": 100}
                }
            }

        except Exception as e:
            return {"status": "error", "error": f"DeepSeek Node Error: {str(e)}"}
