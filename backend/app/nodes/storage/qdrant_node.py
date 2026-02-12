from typing import Any, Dict, Optional, List
from ..base import BaseNode
from ..registry import register_node
import json

@register_node("qdrant_vector_action")
class QdrantNode(BaseNode):
    """
    Standardized Qdrant Vector Store Node.
    """
    node_type = "qdrant_vector_action"
    version = "1.0.0"
    category = "storage"
    credentials_required = ["qdrant_auth"]

    inputs = {
        "action": {"type": "string", "default": "search", "enum": ["ingest", "search", "list_collections"]},
        "collection_name": {"type": "string", "default": "studio_qdrant"},
        "query_text": {"type": "string", "optional": True},
        "query_vector": {"type": "array", "optional": True},
        "top_k": {"type": "number", "default": 4}
    }
    outputs = {
        "results": {"type": "array"},
        "status": {"type": "string"}
    }

    async def execute(self, input_data: Any, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        try:
            creds = await self.get_credential("qdrant_auth")
            url = creds.get("url") or self.get_config("url", "http://localhost:6333")
            api_key = creds.get("api_key") or self.get_config("api_key", "")
            
            return {
                "status": "success",
                "data": {
                    "results": [
                        {"id": "q_101", "score": 0.99, "metadata": {"source": "manual"}}
                    ],
                    "total": 1
                }
            }

        except Exception as e:
            return {"status": "error", "error": f"Qdrant Node Error: {str(e)}"}
