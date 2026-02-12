from typing import Any, Dict, Optional, List
import numpy as np
from langchain_pinecone import PineconeVectorStore
from ..base import BaseNode
from ..registry import register_node

@register_node("pinecone_vectorstore")
class PineconeNode(BaseNode):
    """
    Pinecone Vector Store for high-performance vector search and storage.
    """
    node_type = "pinecone_vectorstore"
    version = "1.0.0"
    category = "vectorstores"
    credentials_required = ["pinecone_auth"]

    inputs = {
        "index_name": {"type": "string", "description": "Pinecone index name"},
        "namespace": {"type": "string", "optional": True},
        "search_query": {"type": "string", "optional": True},
        "top_k": {"type": "number", "default": 4},
        "documents": {"type": "array", "optional": True, "description": "List of LangChain Documents or Data objects to insert"}
    }
    outputs = {
        "results": {"type": "array"},
        "vectorstore": {"type": "object"},
        "status": {"type": "string"}
    }

    async def execute(self, input_data: Any = None, context: Dict[str, Any] = None) -> Dict[str, Any]:
        try:
            # 1. Resolve Embedding Model (must be connected or in context)
            embedding_node = context.get("embeddings") if context else None
            if not embedding_node:
                return {"status": "error", "error": "No Embedding model connected to Pinecone node."}
            
            # If context["embeddings"] is a node instance, call its get_langchain_object
            if hasattr(embedding_node, "get_langchain_object"):
                embeddings = await embedding_node.get_langchain_object(context)
            else:
                embeddings = embedding_node # Assume it's already the object

            # 2. Build Pinecone Instance
            creds = await self.get_credential("pinecone_auth")
            api_key = creds.get("api_key") if creds else self.get_config("pinecone_api_key")
            
            if not api_key:
                return {"status": "error", "error": "Pinecone API Key is required."}

            index_name = self.get_config("index_name")
            namespace = self.get_config("namespace")

            vectorstore = PineconeVectorStore(
                index_name=index_name,
                embedding=embeddings,
                namespace=namespace,
                pinecone_api_key=api_key
            )

            # 3. Handle Operations
            # Mode A: Ingestion
            docs_to_ingest = input_data if isinstance(input_data, list) else self.get_config("documents")
            if docs_to_ingest:
                # Convert to LC Documents if they are the Studio 'Data' objects
                lc_docs = []
                for d in docs_to_ingest:
                    if hasattr(d, "to_lc_document"):
                         lc_docs.append(d.to_lc_document())
                    elif isinstance(d, dict) and "text" in d:
                         from langchain_core.documents import Document
                         lc_docs.append(Document(page_content=d["text"], metadata=d.get("data", {})))
                    else:
                         lc_docs.append(d)
                
                vectorstore.add_documents(lc_docs)

            # Mode B: Search
            query = str(input_data) if isinstance(input_data, str) else self.get_config("search_query")
            results = []
            if query and not docs_to_ingest:
                k = int(self.get_config("top_k", 4))
                docs = vectorstore.similarity_search(query, k=k)
                results = [{"text": d.page_content, "metadata": d.metadata} for d in docs]

            return {
                "status": "success",
                "data": {
                    "results": results,
                    "count": len(results),
                    "vectorstore": vectorstore
                }
            }

        except Exception as e:
            return {"status": "error", "error": f"Pinecone Execution Failed: {str(e)}"}
