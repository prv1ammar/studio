from ..base import BaseNode
from typing import Any, Dict, Optional

class ParseDataNode(BaseNode):
    """
    Converts Data objects/lists into a formatted string (Message) 
    using a user-defined template.
    """
    async def execute(self, input_data: Any = None, context: Optional[Dict[str, Any]] = None) -> str:
        try:
            data_to_parse = input_data
            
            # Resolve Inputs from context/graph if available
            if context and "graph_data" in context:
                graph = context["graph_data"]
                node_id = context["node_id"]
                edges = graph.get("edges", [])
                nodes = graph.get("nodes", [])
                engine = context.get("engine")
                
                # Pull Data
                input_edge = next((e for e in edges if e["target"] == node_id and e["targetHandle"] == "data"), None)
                if input_edge:
                    source_id = input_edge["source"]
                    source_node = next((n for n in nodes if n["id"] == source_id), None)
                    if source_node and engine:
                        print(f"🔄 ParseData: Pulling data from node {source_id}...")
                        data_to_parse = await engine.execute_node(
                            source_node["data"].get("id"), 
                            None, 
                            config=source_node["data"], 
                            context={**context, "node_id": source_id}
                        )
            
            if not data_to_parse:
                return "No context found."
            
            template = self.config.get("template", "{text}")
            sep = self.config.get("sep", "\n\n")
            
            # Normalize to list
            if not isinstance(data_to_parse, list):
                data_to_parse = [data_to_parse]
            
            formatted_parts = []
            for item in data_to_parse:
                if isinstance(item, dict):
                    # Fill template with dict values
                    try:
                        # Extract metadata if nested
                        metadata = item.get("metadata", {})
                        full_dict = {**item, **metadata}
                        formatted_parts.append(template.format(**full_dict))
                    except KeyError as e:
                        # Fallback if key missing
                        print(f"⚠️ ParseData Warning: Missing key {e} for template.")
                        formatted_parts.append(str(item.get("text") or item))
                else:
                    formatted_parts.append(str(item))
            
            result = sep.join(formatted_parts)
            print(f"✅ Formatted {len(formatted_parts)} items into a single message.")
            return result
            
        except Exception as e:
            import traceback
            print(traceback.format_exc())
            return f"Parse Error: {str(e)}"
