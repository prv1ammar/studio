from typing import Any, Dict, List, Optional
from .base import BaseNode

class GenericNode(BaseNode):
    """
    A generic node that handles execution for imported or unimplemented nodes.
    Acts as a standardized fallback/mock implementation.
    """
    version = "1.0.0"
    category = "internal"
    
    def __init__(self, node_type: str, config: Dict[str, Any]):
        super().__init__(config)
        self.node_type = node_type

    async def execute(self, input_data: Any, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Returns a standardized mock response to maintain engine stability."""
        print(f" [GenericNode] Falling back for node_type: {self.node_type}")
        
        result_text = str(input_data)
        if "chat" in self.node_type or "llm" in self.node_type:
             result_text = f"[Generic LLM Response to: {str(input_data)[:30]}...]"
        elif "search" in self.node_type:
            result_text = f"[Generic Search Result for: {str(input_data)[:30]}...]"
            
        return {
            "status": "success",
            "data": {
                "result": result_text,
                "node_type": self.node_type,
                "warning": "This node is using a generic fallback implementation."
            }
        }
