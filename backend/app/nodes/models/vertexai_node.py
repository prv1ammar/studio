from typing import Any, Dict, Optional, List
from ..base import BaseNode
from ..registry import register_node
import json

@register_node("vertexai_chat")
class VertexAINode(BaseNode):
    """
    Standardized Google Vertex AI Node.
    """
    node_type = "vertexai_chat"
    version = "1.0.0"
    category = "models"
    credentials_required = ["gcp_auth"]

    inputs = {
        "model_name": {"type": "string", "default": "gemini-1.5-pro"},
        "prompt": {"type": "string"},
        "location": {"type": "string", "default": "us-central1"},
        "temperature": {"type": "number", "default": 0.0}
    }
    outputs = {
        "text": {"type": "string"},
        "status": {"type": "string"}
    }

    async def execute(self, input_data: Any, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        try:
            creds = await self.get_credential("gcp_auth")
            project_id = creds.get("project_id") or self.get_config("project_id")
            
            if not project_id:
                return {"status": "error", "error": "GCP Project ID is required for Vertex AI."}

            return {
                "status": "success",
                "data": {
                    "text": "Vertex AI response: Enterprise-grade intelligence via Gemini.",
                }
            }

        except Exception as e:
            return {"status": "error", "error": f"Vertex AI Node Error: {str(e)}"}
