from ..base import BaseNode
from typing import Any, Dict, Optional
from langchain_text_splitters import RecursiveCharacterTextSplitter

class SplitTextNode(BaseNode):
    async def execute(self, input_data: Any = None, context: Optional[Dict[str, Any]] = None) -> Any:
        try:
            data_to_split = input_data
            
            # Resolve Inputs from context/graph if available
            if context and "graph_data" in context:
                graph = context["graph_data"]
                node_id = context["node_id"]
                edges = graph.get("edges", [])
                nodes = graph.get("nodes", [])
                engine = context.get("engine")
                
                # Pull Data
                input_edge = next((e for e in edges if e["target"] == node_id and e["targetHandle"] in ["data_inputs", "input"]), None)
                if input_edge:
                    source_id = input_edge["source"]
                    source_node = next((n for n in nodes if n["id"] == source_id), None)
                    if source_node and engine:
                        print(f"🔄 SplitText: Pulling data from node {source_id}...")
                        data_to_split = await engine.execute_node(
                            source_node["data"].get("id"), 
                            None, 
                            config=source_node["data"], 
                            context={**context, "node_id": source_id}
                        )
            
            if not data_to_split:
                return "Error: No data provided to SplitTextNode."
                
            chunk_size = int(self.config.get("chunk_size", 1000))
            chunk_overlap = int(self.config.get("chunk_overlap", 200))
            
            splitter = RecursiveCharacterTextSplitter(
                chunk_size=chunk_size,
                chunk_overlap=chunk_overlap
            )
            
            # Normalize to list
            if not isinstance(data_to_split, list):
                data_to_split = [data_to_split]
                
            results = []
            for item in data_to_split:
                content = ""
                metadata = {}
                
                if isinstance(item, dict):
                    content = item.get("text") or item.get("content") or str(item)
                    metadata = item.get("metadata") or {k: v for k, v in item.items() if k not in ["text", "content"]}
                else:
                    content = str(item)
                
                chunks = splitter.split_text(content)
                for i, chunk in enumerate(chunks):
                    results.append({
                        "text": chunk,
                        "metadata": {**metadata, "chunk_index": i}
                    })
            
            print(f"✅ Split text into {len(results)} chunks.")
            return results
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            raise e
