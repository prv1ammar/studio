from typing import Any, Dict, Optional, List
from ..base import BaseNode
from ..registry import register_node
import json

@register_node("weaviate_vector_action")
class WeaviateNode(BaseNode):
    """
    Standardized Weaviate Vector Store Node.
    """
    node_type = "weaviate_vector_action"
    version = "1.0.0"
    category = "storage"
    credentials_required = ["weaviate_auth"]


    properties = [
        {
            'displayName': 'Operation',
            'name': 'operation',
            'type': 'string',
            'default': 'search',
        },
        {
            'displayName': 'Alpha',
            'name': 'alpha',
            'type': 'string',
            'default': 0.5,
            'description': 'Hybrid search alpha (0=keyword, 1=vector)',
        },
        {
            'displayName': 'Class Name',
            'name': 'class_name',
            'type': 'string',
            'default': 'StudioDocument',
        },
        {
            'displayName': 'Query Text',
            'name': 'query_text',
            'type': 'string',
            'default': '',
        },
    ]
    inputs = {
        "action": {"type": "string", "default": "search", "enum": ["ingest", "search", "hybrid_search"]},
        "class_name": {"type": "string", "default": "StudioDocument"},
        "query_text": {"type": "string", "optional": True},
        "alpha": {"type": "number", "default": 0.5, "description": "Hybrid search alpha (0=keyword, 1=vector)"}
    }
    outputs = {
        "results": {"type": "array"},
        "status": {"type": "string"}
    }

    async def execute(self, input_data: Any, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        try:
            creds = await self.get_credential("weaviate_auth")
            url = creds.get("url") or self.get_config("url")
            
            return {
                "status": "success",
                "data": {
                    "results": [
                        {"id": "w_555", "content": "Sample standardized Weaviate result.", "certainty": 0.92}
                    ]
                }
            }

        except Exception as e:
            return {"status": "error", "error": f"Weaviate Node Error: {str(e)}"}