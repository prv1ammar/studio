from typing import Any, Dict, Optional, List
from langchain_openai import OpenAIEmbeddings
from ..base import BaseNode
from ..registry import register_node

@register_node("openai_embeddings")
class OpenAIEmbeddingsNode(BaseNode):
    """
    Generate embeddings using OpenAI models.
    """
    node_type = "openai_embeddings"
    version = "1.0.0"
    category = "embeddings"
    credentials_required = ["openai_auth"]

    inputs = {
        "model": {"type": "string", "default": "text-embedding-3-small"},
        "dimensions": {"type": "number", "optional": True},
        "openai_api_key": {"type": "string", "optional": True}
    }
    outputs = {
        "embeddings_object": {"type": "object"},
        "status": {"type": "string"}
    }

    async def execute(self, input_data: Any = None, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        In the new architecture, embedding nodes primarily provide the embedding object 
        to other nodes (like Vector Stores), but can also be used to embed text directly.
        """
        try:
            embeddings = await self.get_langchain_object(context)
            
            # If input_data is provided (e.g. text or list of texts), perform embedding
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
            return {"status": "error", "error": f"OpenAI Embeddings Failed: {str(e)}"}

    async def get_langchain_object(self, context: Optional[Dict[str, Any]] = None) -> Any:
        # 1. Resolve Credentials
        creds = await self.get_credential("openai_auth")
        api_key = creds.get("api_key") if creds else self.get_config("openai_api_key")
        
        if not api_key:
            raise ValueError("OpenAI API Key is required for Embeddings.")

        # 2. Build Object
        return OpenAIEmbeddings(
            openai_api_key=api_key,
            model=self.get_config("model", "text-embedding-3-small"),
            dimensions=self.get_config("dimensions")
        )
