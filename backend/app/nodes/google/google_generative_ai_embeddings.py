from typing import Any, Dict, Optional, List
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from ..base import BaseNode
from ..registry import register_node

@register_node("google_embeddings")
class GoogleEmbeddingsNode(BaseNode):
    """
    Generate embeddings using Google Generative AI models.
    """
    node_type = "google_embeddings"
    version = "1.0.0"
    category = "embeddings"
    credentials_required = ["google_auth"]

    inputs = {
        "model": {"type": "string", "default": "models/text-embedding-004"},
        "api_key": {"type": "string", "optional": True}
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
            return {"status": "error", "error": f"Google Embeddings Failed: {str(e)}"}

    async def get_langchain_object(self, context: Optional[Dict[str, Any]] = None) -> Any:
        # 1. Resolve Credentials
        creds = await self.get_credential("google_auth")
        api_key = creds.get("api_key") if creds else self.get_config("api_key")
        
        if not api_key:
             raise ValueError("Google API Key is required for Embeddings.")

        # 2. Build Object
        return GoogleGenerativeAIEmbeddings(
            google_api_key=api_key,
            model=self.get_config("model", "models/text-embedding-004")
        )
