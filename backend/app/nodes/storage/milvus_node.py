from typing import Any, Dict, Optional, List
from ..base import BaseNode
from ..registry import register_node
import json

@register_node("milvus_vector_action")
class MilvusNode(BaseNode):
    """
    Standardized Milvus Vector Store Node.
    """
    node_type = "milvus_vector_action"
    version = "1.0.0"
    category = "storage"
    credentials_required = ["milvus_auth"]


    properties = [
        {
            'displayName': 'Operation',
            'name': 'operation',
            'type': 'string',
            'default': 'search',
        },
        {
            'displayName': 'Collection Name',
            'name': 'collection_name',
            'type': 'string',
            'default': 'studio_collection',
        },
        {
            'displayName': 'Data',
            'name': 'data',
            'type': 'string',
            'default': '',
        },
        {
            'displayName': 'Query Text',
            'name': 'query_text',
            'type': 'string',
            'default': '',
        },
        {
            'displayName': 'Query Vector',
            'name': 'query_vector',
            'type': 'string',
            'default': '',
        },
        {
            'displayName': 'Top K',
            'name': 'top_k',
            'type': 'string',
            'default': 4,
        },
    ]
    inputs = {
        "action": {"type": "string", "default": "search", "enum": ["ingest", "search", "delete_collection"]},
        "collection_name": {"type": "string", "default": "studio_collection"},
        "query_vector": {"type": "array", "optional": True},
        "query_text": {"type": "string", "optional": True},
        "data": {"type": "any", "optional": True},
        "top_k": {"type": "number", "default": 4}
    }
    outputs = {
        "results": {"type": "array"},
        "status": {"type": "string"}
    }

    async def execute(self, input_data: Any, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        try:
            creds = await self.get_credential("milvus_auth")
            uri = creds.get("uri") or self.get_config("uri", "http://localhost:19530")
            token = creds.get("token") or self.get_config("token", "")
            
            action = self.get_config("action", "search")
            
            # Implementation would use pymilvus or langchain-milvus
            return {
                "status": "success",
                "data": {
                    "results": [
                        {"id": "doc_1", "score": 0.98, "content": "Sample standardized vector result."},
                        {"id": "doc_2", "score": 0.95, "content": "Another match from Milvus."}
                    ],
                    "total": 2
                }
            }

        except Exception as e:
            return {"status": "error", "error": f"Milvus Node Error: {str(e)}"}