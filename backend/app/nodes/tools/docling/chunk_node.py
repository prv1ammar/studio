from ...base import BaseNode
from typing import Any, Dict, Optional
import json
import traceback

class ChunkDoclingNode(BaseNode):
    async def execute(self, input_data: Any = None, context: Optional[Dict[str, Any]] = None) -> Any:
        try:
            data_to_chunk = input_data
            
            # Resolve Inputs from graph/context
            if context and "graph_data" in context:
                from app.nodes.factory import NodeFactory
                factory = NodeFactory()
                graph = context["graph_data"]
                node_id = context["node_id"]
                edges = graph.get("edges", [])
                
                input_edge = next((e for e in edges if e["target"] == node_id and e["targetHandle"] in ["data_inputs", "input"]), None)
                if input_edge and context.get("engine"):
                    source_id = input_edge["source"]
                    source_node = next((n for n in graph["nodes"] if n["id"] == source_id), None)
                    if source_node:
                        data_to_chunk = await context["engine"].execute_node(
                            source_node["data"].get("id"), 
                            None, 
                            config=source_node["data"], 
                            context={**context, "node_id": source_id}
                        )
            
            if not data_to_chunk:
                return "Error: No data to chunk."
                
            # Handle DataFrame
            import pandas as pd
            if isinstance(data_to_chunk, pd.DataFrame):
                data_to_chunk = data_to_chunk.to_dict(orient="records")
            elif not isinstance(data_to_chunk, list):
                data_to_chunk = [data_to_chunk]
                
            results = []
            chunk_size = self.config.get("chunk_size", 2000)
            chunk_overlap = self.config.get("chunk_overlap", 200)
            
            # Use LangChain splitter as fallback for Enriched Markdown
            from langchain_text_splitters import RecursiveCharacterTextSplitter
            splitter = RecursiveCharacterTextSplitter(
                chunk_size=chunk_size,
                chunk_overlap=chunk_overlap,
                separators=["\n\n", "\n", " ", ""]
            )

            for index, item in enumerate(data_to_chunk):
                print(f"📦 Chunk Processing Item {index}: Type={type(item)}")
                
                if isinstance(item, dict):
                    text_content = item.get("text", "")
                    doc_obj = item.get("doc_object")
                    metadata = item.get("metadata", {})
                else:
                    text_content = str(item)
                    doc_obj = None
                    metadata = {}

                # Intelligent Choice:
                if text_content and ("![" in text_content or self.config.get("force_text_chunking")):
                    print("🧠 ChunkDocling: Using Enriched Text splitting...")
                    chunks = splitter.split_text(text_content)
                    for i, chunk_text in enumerate(chunks):
                        results.append({
                            "text": chunk_text,
                            "metadata": {
                                **metadata,
                                "chunk_index": i,
                                "method": "enriched_text"
                            }
                        })
                # Otherwise use the Docling Hierarchical Chunker if doc_obj is available
                elif doc_obj:
                    from docling_core.transforms.chunker.hierarchical_chunker import HierarchicalChunker
                    chunker = HierarchicalChunker()
                    print(f"📄 ChunkDocling: Using Hierarchical Chunker...")
                    
                    c_idx = 0
                    for chunk in chunker.chunk(dl_doc=doc_obj):
                        results.append({
                            "text": chunker.contextualize(chunk=chunk),
                            "metadata": {
                                **metadata,
                                "chunk_index": c_idx,
                                "method": "hierarchical"
                            }
                        })
                        c_idx += 1
                else:
                    # Basic fallback
                    results.append({"text": text_content, "metadata": metadata})
            
            return results
            
        except Exception as e:
            traceback.print_exc()
            return f"Chunking Error: {str(e)}"

    async def get_langchain_object(self, context: Optional[Dict[str, Any]] = None) -> Any:
        return None
