"""
Loop Over Items Node - Studio Standard (Universal Method)
Batch 93: Advanced Workflow (n8n Critical)
"""
from typing import Any, Dict, Optional, List
from ..base import BaseNode
from ..registry import register_node

@register_node("loop_node")
class LoopNode(BaseNode):
    """
    Iterate over items in a list.
    Essential for processing arrays one by one.
    """
    node_type = "loop_node"
    version = "1.0.0"
    category = "flow_control"
    credentials_required = []


    properties = [
        {
            'displayName': 'Batch Size',
            'name': 'batch_size',
            'type': 'string',
            'default': 1,
            'description': 'Number of items per iteration',
        },
        {
            'displayName': 'Data',
            'name': 'data',
            'type': 'string',
            'default': '',
            'description': 'List of items to iterate over',
        },
    ]
    inputs = {
        "batch_size": {
            "type": "number",
            "default": 1,
            "description": "Number of items per iteration"
        },
        "data": {
            "type": "any",
            "description": "List of items to iterate over"
        }
    }

    outputs = {
        "item": {"type": "any"},
        "index": {"type": "number"},
        "status": {"type": "string"}
    }

    async def execute(self, input_data: Any, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        try:
            batch_size = int(self.get_config("batch_size", 1))
            
            # Get data to iterate
            data = input_data
            if not isinstance(data, list):
                data = [data]
            
            # This node is special - it signals the execution engine to loop
            # In a real engine, this would yield results.
            # For our standard execution, we return the structure that the engine expects
            # to handle looping.
            
            return {
                "status": "success",
                "data": {
                    "result": data,
                    "batch_size": batch_size,
                    "is_loop": True,
                    "total_items": len(data)
                }
            }

        except Exception as e:
            return {"status": "error", "error": f"Loop Node Failed: {str(e)}"}