"""
FAISS Vector Store Node - Studio Standard
Batch 32: Vector Store Nodes
"""
from typing import Any, Dict, Optional, List
from pathlib import Path
from ..base import BaseNode
from ..registry import register_node

@register_node("faiss_vectorstore")
class FAISSNode(BaseNode):
    """
    FAISS (Facebook AI Similarity Search) Vector Store.
    High-performance local vector search with persistence.
    """
    node_type = "faiss_vectorstore"
    version = "1.0.0"
    category = "vectorstores"
    credentials_required = []


    properties = [
        {
            'displayName': 'Allow Dangerous Deserialization',
            'name': 'allow_dangerous_deserialization',
            'type': 'boolean',
            'default': False,
            'description': 'Allow loading pickle files (only if you trust the source)',
        },
        {
            'displayName': 'Documents',
            'name': 'documents',
            'type': 'string',
            'default': '',
            'description': 'Documents to ingest into the vector store',
        },
        {
            'displayName': 'Index Name',
            'name': 'index_name',
            'type': 'string',
            'default': 'studio_index',
            'description': 'Name of the FAISS index',
        },
        {
            'displayName': 'Persist Directory',
            'name': 'persist_directory',
            'type': 'string',
            'default': '',
            'description': 'Directory to save/load the FAISS index',
        },
        {
            'displayName': 'Search Query',
            'name': 'search_query',
            'type': 'string',
            'default': '',
            'description': 'Query text for similarity search',
        },
        {
            'displayName': 'Top K',
            'name': 'top_k',
            'type': 'string',
            'default': 4,
            'description': 'Number of results to return',
        },
    ]
    inputs = {
        "index_name": {
            "type": "string",
            "default": "studio_index",
            "description": "Name of the FAISS index"
        },
        "persist_directory": {
            "type": "string",
            "optional": True,
            "description": "Directory to save/load the FAISS index"
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
        "allow_dangerous_deserialization": {
            "type": "boolean",
            "default": False,
            "description": "Allow loading pickle files (only if you trust the source)"
        }
    }

    outputs = {
        "results": {"type": "array"},
        "count": {"type": "number"},
        "vectorstore": {"type": "object"},
        "index_path": {"type": "string"}
    }

    async def execute(self, input_data: Any, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        try:
            # Import dependencies
            try:
                from langchain_community.vectorstores import FAISS
            except ImportError:
                return {
                    "status": "error",
                    "error": "langchain-community not installed. Run: pip install langchain-community"
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
            index_name = self.get_config("index_name", "studio_index")
            persist_dir = self.get_config("persist_directory")
            allow_dangerous = self.get_config("allow_dangerous_deserialization", False)

            # Resolve persist directory
            if persist_dir:
                path = Path(persist_dir).resolve()
                path.mkdir(parents=True, exist_ok=True)
            else:
                path = Path.cwd() / ".faiss_indexes"
                path.mkdir(parents=True, exist_ok=True)

            index_path = path / f"{index_name}.faiss"

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

                # Create FAISS index from documents
                vectorstore = FAISS.from_documents(
                    documents=lc_docs,
                    embedding=embeddings
                )

                # Save to disk
                vectorstore.save_local(str(path), index_name)

                return {
                    "status": "success",
                    "data": {
                        "results": [],
                        "count": len(lc_docs),
                        "vectorstore": vectorstore,
                        "index_path": str(index_path),
                        "message": f"Ingested {len(lc_docs)} documents and saved to {index_path}"
                    }
                }

            # Handle search query
            query = str(input_data) if isinstance(input_data, str) else self.get_config("search_query")
            
            if query:
                # Load existing index or create empty one
                if index_path.exists():
                    try:
                        vectorstore = FAISS.load_local(
                            folder_path=str(path),
                            embeddings=embeddings,
                            index_name=index_name,
                            allow_dangerous_deserialization=allow_dangerous
                        )
                    except Exception as e:
                        return {
                            "status": "error",
                            "error": f"Failed to load FAISS index: {str(e)}. Try setting allow_dangerous_deserialization=True if you trust the source."
                        }
                else:
                    return {
                        "status": "error",
                        "error": f"FAISS index not found at {index_path}. Ingest documents first."
                    }

                # Perform similarity search
                k = int(self.get_config("top_k", 4))
                docs = vectorstore.similarity_search(query, k=k)
                
                results = [
                    {
                        "text": d.page_content,
                        "metadata": d.metadata
                    }
                    for d in docs
                ]

                return {
                    "status": "success",
                    "data": {
                        "results": results,
                        "count": len(results),
                        "vectorstore": vectorstore,
                        "index_path": str(index_path)
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
                "error": f"FAISS execution failed: {str(e)}"
            }