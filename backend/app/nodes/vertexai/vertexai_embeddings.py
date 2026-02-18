from typing import Any, Dict, Optional, List
from ..base import BaseNode
from ..registry import register_node

@register_node("vertexai_embeddings")
class VertexAIEmbeddingsNode(BaseNode):
    """
    Generate embeddings using Vertex AI (Google Cloud).
    """
    node_type = "vertexai_embeddings"
    version = "1.0.0"
    category = "embeddings"
    credentials_required = ["gcp_auth"]


    properties = [
        {
            'displayName': 'Location',
            'name': 'location',
            'type': 'string',
            'default': 'us-central1',
        },
        {
            'displayName': 'Model',
            'name': 'model',
            'type': 'string',
            'default': 'textembedding-gecko',
        },
        {
            'displayName': 'Project',
            'name': 'project',
            'type': 'string',
            'default': '',
        },
    ]
    inputs = {
        "model": {"type": "string", "default": "textembedding-gecko"},
        "project": {"type": "string", "optional": True},
        "location": {"type": "string", "default": "us-central1"}
    }
    outputs = {
        "embeddings_object": {"type": "object"},
        "status": {"type": "string"}
    }

    async def execute(self, input_data: Any = None, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        try:
            embeddings = await self.get_langchain_object(context)
            
            result_data = {}
            if input_data:
                if isinstance(input_data, str):
                    result_data["embedding"] = embeddings.embed_query(input_data)
                elif isinstance(input_data, list):
                    result_data["embeddings"] = embeddings.embed_documents(input_data)

            return {
                "status": "success",
                "data": {
                    "embeddings_object": embeddings,
                    **result_data
                }
            }
        except Exception as e:
            return {"status": "error", "error": f"Vertex AI Embeddings Failed: {str(e)}"}

    async def get_langchain_object(self, context: Optional[Dict[str, Any]] = None) -> Any:
        try:
            from langchain_google_vertexai import VertexAIEmbeddings
        except ImportError:
            raise ImportError("Please install 'langchain-google-vertexai' to use Vertex AI Embeddings.")

        # 1. Resolve Credentials
        creds = await self.get_credential("gcp_auth")
        
        # 2. Build Object
        # vertexai usually uses GOOGLE_APPLICATION_CREDENTIALS env var or service account info
        return VertexAIEmbeddings(
            model_name=self.get_config("model", "textembedding-gecko"),
            project=self.get_config("project") or (creds.get("project_id") if creds else None),
            location=self.get_config("location", "us-central1")
        )