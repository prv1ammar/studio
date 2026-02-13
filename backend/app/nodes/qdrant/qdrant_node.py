"""
Qdrant Vector Store Node - Studio Standard
Batch 32: Vector Store Nodes
"""
from typing import Any, Dict, Optional, List
from ...base import BaseNode
from ...registry import register_node

@register_node("qdrant_vectorstore")
class QdrantNode(BaseNode):
    """
    Qdrant Vector Store with search capabilities.
    Supports both cloud and self-hosted Qdrant instances.
    """
    node_type = "qdrant_vectorstore"
    version = "1.0.0"
    category = "vectorstores"
    credentials_required = []  # API key optional for local

    inputs = {
        "collection_name": {
            "type": "string",
            "required": True,
            "description": "Name of the Qdrant collection"
        },
        "url": {
            "type": "string",
            "optional": True,
            "description": "Qdrant server URL (e.g., https://xyz.qdrant.io)"
        },
        "host": {
            "type": "string",
            "default": "localhost",
            "description": "Qdrant host for self-hosted instances"
        },
        "port": {
            "type": "number",
            "default": 6333,
            "description": "Qdrant HTTP port"
        },
        "grpc_port": {
            "type": "number",
            "default": 6334,
            "description": "Qdrant gRPC port"
        },
        "api_key": {
            "type": "string",
            "optional": True,
            "description": "Qdrant API key (required for cloud)"
        },
        "distance_func": {
            "type": "dropdown",
            "default": "Cosine",
            "options": ["Cosine", "Euclidean", "Dot Product"],
            "description": "Distance function for similarity"
        },
        "search_query": {
            "type": "string",
            "optional": True,
            "description": "Query text for similarity search"
        },
        "top_k": {
            "type": "number",
            "default": 4,
            "description": "Number of results to return"
        },
        "documents": {
            "type": "array",
            "optional": True,
            "description": "Documents to ingest into the vector store"
        },
        "path": {
            "type": "string",
            "optional": True,
            "description": "Local path for persistent storage"
        }
    }

    outputs = {
        "results": {"type": "array"},
        "count": {"type": "number"},
        "vectorstore": {"type": "object"}
    }

    async def execute(self, input_data: Any, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        try:
            # Import dependencies
            try:
                from langchain_community.vectorstores import Qdrant
                from qdrant_client import QdrantClient
            except ImportError as e:
                missing = "langchain-community" if "langchain" in str(e) else "qdrant-client"
                return {
                    "status": "error",
                    "error": f"{missing} not installed. Run: pip install {missing}"
                }

            # Get embedding model from context
            embedding_node = context.get("embeddings") if context else None
            if not embedding_node:
                return {
                    "status": "error",
                    "error": "No embedding model connected. Connect an embedding node first."
                }

            # Resolve embeddings
            if hasattr(embedding_node, "get_langchain_object"):
                embeddings = await embedding_node.get_langchain_object(context)
            else:
                embeddings = embedding_node

            # Get configuration
            collection_name = self.get_config("collection_name")
            if not collection_name:
                return {"status": "error", "error": "Collection name is required"}

            # Build server connection parameters
            server_kwargs = {}
            
            # Cloud URL takes precedence
            url = self.get_config("url")
            if url:
                server_kwargs["url"] = url
                api_key = self.get_config("api_key")
                if api_key:
                    server_kwargs["api_key"] = api_key
            else:
                # Self-hosted configuration
                server_kwargs["host"] = self.get_config("host", "localhost")
                server_kwargs["port"] = int(self.get_config("port", 6333))
                server_kwargs["grpc_port"] = int(self.get_config("grpc_port", 6334))
                
                # Optional path for local persistence
                path = self.get_config("path")
                if path:
                    server_kwargs["path"] = path

            # Build Qdrant kwargs
            qdrant_kwargs = {
                "collection_name": collection_name,
                "content_payload_key": "page_content",
                "metadata_payload_key": "metadata"
            }

            # Handle document ingestion
            docs_to_ingest = input_data if isinstance(input_data, list) else self.get_config("documents")
            
            if docs_to_ingest:
                # Convert to LangChain documents
                lc_docs = []
                for d in docs_to_ingest:
                    if hasattr(d, "to_lc_document"):
                        lc_docs.append(d.to_lc_document())
                    elif isinstance(d, dict) and "text" in d:
                        from langchain_core.documents import Document
                        lc_docs.append(Document(
                            page_content=d["text"],
                            metadata=d.get("metadata", {})
                        ))
                    else:
                        lc_docs.append(d)

                # Create vector store with documents
                vectorstore = Qdrant.from_documents(
                    lc_docs,
                    embedding=embeddings,
                    **qdrant_kwargs,
                    **server_kwargs
                )
                
                return {
                    "status": "success",
                    "data": {
                        "results": [],
                        "count": len(lc_docs),
                        "vectorstore": vectorstore,
                        "message": f"Ingested {len(lc_docs)} documents"
                    }
                }

            # Handle search query
            query = str(input_data) if isinstance(input_data, str) else self.get_config("search_query")
            
            if query:
                # Create client and vector store for search
                client = QdrantClient(**server_kwargs)
                vectorstore = Qdrant(
                    client=client,
                    embeddings=embeddings,
                    **qdrant_kwargs
                )

                # Perform similarity search
                k = int(self.get_config("top_k", 4))
                docs = vectorstore.similarity_search(query, k=k)
                
                results = [
                    {
                        "text": d.page_content,
                        "metadata": d.metadata,
                        "score": getattr(d, "score", None)
                    }
                    for d in docs
                ]

                return {
                    "status": "success",
                    "data": {
                        "results": results,
                        "count": len(results),
                        "vectorstore": vectorstore
                    }
                }

            # No operation specified
            return {
                "status": "error",
                "error": "Provide either 'documents' for ingestion or 'search_query' for search"
            }

        except Exception as e:
            return {
                "status": "error",
                "error": f"Qdrant execution failed: {str(e)}"
            }
