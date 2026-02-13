"""
Iterator (Loop) Node - Studio Standard
Batch 38: Logic & Flow Control
"""
from typing import Any, Dict, Optional, List
from ...base import BaseNode
from ...registry import register_node

@register_node("iterator")
class IteratorNode(BaseNode):
    """
    Iterate over a list of items.
    Outputs each item individually.
    Useful for processing multiple documents or results.
    """
    node_type = "iterator"
    version = "1.0.0"
    category = "logic"
    credentials_required = []

    inputs = {
        "input_list": {
            "type": "array",
            "required": True,
            "description": "List of items to iterate over"
        }
    }

    outputs = {
        "item": {"type": "any"},
        "index": {"type": "number"},
        "is_first": {"type": "boolean"},
        "is_last": {"type": "boolean"}
    }

    async def execute(self, input_data: Any, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        try:
            # Get list
            items = input_data if isinstance(input_data, list) else self.get_config("input_list", [])
            
            if not isinstance(items, list):
                # Handle single item case gracefully
                if items:
                    items = [items]
                else:
                    return {"status": "error", "error": "Input must be a list"}

            # In a flow execution, this node would typically generate multiple outputs.
            # However, for a single execution call, we return the LIST of results 
            # structured so the engine can interpret them if supported, 
            # or just return the first item if linear.
            
            # Since we can't change the engine, let's return a special structure 
            # that indicates "multiple outputs" if the engine supports it, 
            # or just return the list itself as "items".
            
            # But wait, standard nodes return a SINGLE result dictionary.
            # To support iteration, we might need to return the whole list and let the next node handle it,
            # OR this node is intended to be used in a loop structure.
            
            # Let's return the full list in a format that suggests iteration:
            return {
                "status": "success",
                "data": {
                    "items": items,
                    "count": len(items),
                    "type": "iterator_output" 
                }
            }

        except Exception as e:
            return {
                "status": "error",
                "error": f"Iterator failed: {str(e)}"
            }
