"""
Cohere Embeddings Node - Studio Standard
Batch 33: Embedding Models
"""
from typing import Any, Dict, Optional, List
from ...base import BaseNode
from ...registry import register_node

@register_node("cohere_embeddings")
class CohereEmbeddingsNode(BaseNode):
    """
    Generate embeddings using Cohere models.
    Supports English and multilingual embedding models.
    """
    node_type = "cohere_embeddings"
    version = "1.0.0"
    category = "embeddings"
    credentials_required = ["cohere_auth"]

    inputs = {
        "model_name": {
            "type": "dropdown",
            "default": "embed-english-v3.0",
            "options": [
                "embed-english-v3.0",
                "embed-multilingual-v3.0",
                "embed-english-light-v3.0",
                "embed-multilingual-light-v3.0",
                "embed-english-v2.0",
                "embed-multilingual-v2.0"
            ],
            "description": "Cohere embedding model to use"
        },
        "input_type": {
            "type": "dropdown",
            "default": "search_document",
            "options": ["search_document", "search_query", "classification", "clustering"],
            "description": "Type of input for optimal embeddings"
        },
        "truncate": {
            "type": "dropdown",
            "default": "END",
            "options": ["NONE", "START", "END"],
            "description": "How to truncate text if too long"
        },
        "max_retries": {
            "type": "number",
            "default": 3,
            "description": "Maximum number of API retries"
        },
        "request_timeout": {
            "type": "number",
            "default": 60,
            "description": "Request timeout in seconds"
        }
    }

    outputs = {
        "embeddings_object": {"type": "object"},
        "embedding": {"type": "array"},
        "embeddings": {"type": "array"}
    }

    async def execute(self, input_data: Any, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Embedding nodes provide the embedding object to other nodes (like Vector Stores),
        but can also be used to embed text directly.
        """
        try:
            embeddings = await self.get_langchain_object(context)
            
            # If input_data is provided, perform embedding
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
            return {
                "status": "error",
                "error": f"Cohere Embeddings failed: {str(e)}"
            }

    async def get_langchain_object(self, context: Optional[Dict[str, Any]] = None) -> Any:
        """Get the LangChain embeddings object for use by other nodes."""
        try:
            from langchain_cohere import CohereEmbeddings
        except ImportError:
            raise ImportError("langchain-cohere not installed. Run: pip install langchain-cohere")

        # Get credentials
        creds = await self.get_credential("cohere_auth")
        api_key = creds.get("api_key") if creds else self.get_config("cohere_api_key")
        
        if not api_key:
            raise ValueError("Cohere API Key is required for embeddings")

        # Get configuration
        model_name = self.get_config("model_name", "embed-english-v3.0")
        truncate = self.get_config("truncate", "END")
        max_retries = int(self.get_config("max_retries", 3))
        request_timeout = self.get_config("request_timeout", 60)

        # Build embeddings object
        try:
            embeddings = CohereEmbeddings(
                cohere_api_key=api_key,
                model=model_name,
                truncate=truncate,
                max_retries=max_retries,
                user_agent="studio",
                request_timeout=request_timeout if request_timeout else None
            )
            return embeddings
        except Exception as e:
            raise ValueError(
                f"Unable to create Cohere Embeddings. "
                f"Please verify the API key and model parameters. Error: {str(e)}"
            )
