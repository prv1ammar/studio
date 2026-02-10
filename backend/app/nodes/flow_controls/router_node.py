from typing import Any, Dict, Optional
from ..base import BaseNode
import re

class RouterNode(BaseNode):
    """
    BaseNode compatible implementation of the Conditional Router.
    """
    
    async def execute(self, input_data: Any, context: Optional[Dict[str, Any]] = None) -> Any:
        # Extract configuration
        match_text = str(self.config.get("match_text", "")).strip()
        operator = self.config.get("operator", "equals")
        case_sensitive = self.config.get("case_sensitive", True)
        
        # Handle input (extract intent/text from common keys)
        input_text = ""
        if isinstance(input_data, dict):
            input_text = (
                input_data.get("intent") or 
                input_data.get("input_text") or 
                input_data.get("input") or 
                input_data.get("text") or 
                str(input_data)
            )
        else:
            input_text = str(input_data)
            
        input_text = input_text.strip()
        
        # Perform comparison
        result = False
        
        # Casing
        comp_input = input_text if case_sensitive else input_text.lower()
        comp_match = match_text if case_sensitive else match_text.lower()
        
        if operator == "equals":
            result = comp_input == comp_match
        elif operator == "not equals":
            result = comp_input != comp_match
        elif operator == "contains":
            result = comp_match in comp_input
        elif operator == "starts with":
            result = comp_input.startswith(comp_match)
        elif operator == "ends with":
            result = comp_input.endswith(comp_match)
        elif operator == "regex":
            try:
                result = bool(re.match(match_text, input_text))
            except:
                result = False
        
        print(f"[RouterNode] Comparing '{input_text}' {operator} '{match_text}' -> {result}")
        
        # Traversal Logic:
        # We need to find the specific target node ID for the 'True' or 'False' branch.
        routes = context.get("routes", []) if context else []
        
        # The edges in the graph have 'sourceHandle' which is "true_result" or "false_result"
        # The engine.py process_workflow collects 'outgoing' edges.
        
        # IMPORTANT: Since this engine.py is simple, we return the target_id 
        # so the engine knows which node to hop to next.
        
        # Find edges for this node
        graph_data = context.get("graph_data", {})
        edges = graph_data.get("edges", [])
        node_id = context.get("node_id")
        
        target_handle = "true_result" if result else "false_result"
        
        # Find the node ID connected to this specific handle
        next_node_id = None
        for edge in edges:
            if edge["source"] == node_id and edge.get("sourceHandle") == target_handle:
                next_node_id = edge["target"]
                break
                
        if not next_node_id:
            print(f"[RouterNode] Warning: No target found for handle '{target_handle}'")
            return f"No path found for {target_handle}"
            
        print(f"[RouterNode] Routing to node: {next_node_id}")
        return next_node_id
