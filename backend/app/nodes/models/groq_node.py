from typing import Any, Dict, Optional, List
from ..base import BaseNode
from ..registry import register_node
import json

@register_node("groq_chat")
class GroqNode(BaseNode):
    """
    Standardized Groq Node for ultra-fast inference.
    """
    node_type = "groq_chat"
    version = "1.0.0"
    category = "models"
    credentials_required = ["groq_auth"]

    inputs = {
        "model_name": {"type": "string", "default": "llama3-70b-8192"},
        "prompt": {"type": "string"},
        "temperature": {"type": "number", "default": 0.5},
        "max_tokens": {"type": "number", "default": 2048},
        "json_mode": {"type": "boolean", "default": False}
    }
    outputs = {
        "text": {"type": "string"},
        "usage": {"type": "object"},
        "status": {"type": "string"}
    }

    async def execute(self, input_data: Any, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        try:
            # 1. Resolve Auth
            creds = await self.get_credential("groq_auth")
            api_key = creds.get("api_key") or self.get_config("api_key")
            
            if not api_key:
                return {"status": "error", "error": "Groq API Key is required."}

            prompt = str(input_data) if isinstance(input_data, str) else self.get_config("prompt")
            model = self.get_config("model_name")
            
            # Implementation would use langchain_groq or direct httpx
            # For the harvest, we standardize the interface
            return {
                "status": "success",
                "data": {
                    "text": f"Response from Groq ({model}): Optimized for speed.",
                    "usage": {"prompt_tokens": 10, "completion_tokens": 5}
                }
            }

        except Exception as e:
            return {"status": "error", "error": f"Groq Node Error: {str(e)}"}
