from typing import Any, Dict, Optional, List
from langchain_chroma import Chroma
from ..base import BaseNode
from ..registry import register_node

@register_node("chroma_vectorstore")
class ChromaNode(BaseNode):
    """
    Chroma Vector Store (Native/Local and Server support).
    """
    node_type = "chroma_vectorstore"
    version = "1.0.0"
    category = "vectorstores"

    inputs = {
        "collection_name": {"type": "string", "default": "studio_collection"},
        "persist_directory": {"type": "string", "optional": True},
        "search_query": {"type": "string", "optional": True},
        "top_k": {"type": "number", "default": 4},
        "documents": {"type": "array", "optional": True}
    }
    outputs = {
        "results": {"type": "array"},
        "vectorstore": {"type": "object"},
        "status": {"type": "string"}
    }

    async def execute(self, input_data: Any = None, context: Dict[str, Any] = None) -> Dict[str, Any]:
        try:
            # 1. Resolve Embedding Model
            embedding_node = context.get("embeddings") if context else None
            if not embedding_node:
                return {"status": "error", "error": "No Embedding model connected to Chroma node."}
            
            if hasattr(embedding_node, "get_langchain_object"):
                embeddings = await embedding_node.get_langchain_object(context)
            else:
                embeddings = embedding_node

            # 2. Build Chroma Instance
            collection_name = self.get_config("collection_name", "studio_collection")
            persist_dir = self.get_config("persist_directory")
            
            # TODO: Add server support (host/port) if needed by reading config
            
            vectorstore = Chroma(
                collection_name=collection_name,
                embedding_function=embeddings,
                persist_directory=persist_dir
            )

            # 3. Handle Operations
            # Mode A: Ingestion
            docs_to_ingest = input_data if isinstance(input_data, list) else self.get_config("documents")
            if docs_to_ingest:
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
            return {"status": "error", "error": f"Chroma Execution Failed: {str(e)}"}
