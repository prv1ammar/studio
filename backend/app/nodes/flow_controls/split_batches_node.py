"""
Split In Batches Node - Studio Standard (Universal Method)
Batch 89: Core Workflow Nodes
"""
from typing import Any, Dict, Optional, List
from ..base import BaseNode
from ..registry import register_node

@register_node("split_batches_node")
class SplitBatchesNode(BaseNode):
    """
    Split large datasets into smaller batches for processing.
    Essential for handling rate limits and memory management.
    """
    node_type = "split_batches_node"
    version = "1.0.0"
    category = "flow_control"
    credentials_required = []


    properties = [
        {
            'displayName': 'Batch Size',
            'name': 'batch_size',
            'type': 'string',
            'default': 10,
            'description': 'Number of items per batch',
        },
        {
            'displayName': 'Data',
            'name': 'data',
            'type': 'string',
            'default': '',
            'description': 'Data to split into batches',
        },
    ]
    inputs = {
        "batch_size": {
            "type": "number",
            "default": 10,
            "description": "Number of items per batch"
        },
        "data": {
            "type": "any",
            "description": "Data to split into batches"
        }
    }

    outputs = {
        "batch": {"type": "any"},
        "batch_index": {"type": "number"},
        "total_batches": {"type": "number"},
        "status": {"type": "string"}
    }

    async def execute(self, input_data: Any, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        try:
            batch_size = int(self.get_config("batch_size", 10))
            
            # Get data to split
            data = input_data
            if not isinstance(data, list):
                data = [data]
            
            # Calculate batches
            total_items = len(data)
            total_batches = (total_items + batch_size - 1) // batch_size  # Ceiling division
            
            # Split into batches
            batches = []
            for i in range(0, total_items, batch_size):
                batch = data[i:i + batch_size]
                batches.append({
                    "batch": batch,
                    "batch_index": len(batches),
                    "total_batches": total_batches,
                    "batch_size": len(batch),
                    "total_items": total_items
                })
            
            return {
                "status": "success",
                "data": {
                    "result": batches,
                    "total_batches": total_batches,
                    "total_items": total_items
                }
            }

        except Exception as e:
            return {"status": "error", "error": f"Split Batches Node Failed: {str(e)}"}