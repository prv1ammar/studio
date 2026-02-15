"""
Split In Batches Node - Studio Standard (Universal Method)
Batch 103: Core Workflow Nodes
"""
from typing import Any, Dict, Optional, List
from ...base import BaseNode
from ...registry import register_node

@register_node("split_in_batches_node")
class SplitInBatchesNode(BaseNode):
    """
    Loop over items in batches for processing large datasets.
    """
    node_type = "split_in_batches_node"
    version = "1.0.0"
    category = "flow_controls"
    credentials_required = []

    inputs = {
        "batch_size": {
            "type": "number",
            "default": 10,
            "description": "Number of items per batch"
        },
        "items": {
            "type": "any",
            "optional": True,
            "description": "Items to split into batches"
        },
        "reset": {
            "type": "boolean",
            "default": False,
            "optional": True,
            "description": "Reset batch counter"
        }
    }

    outputs = {
        "result": {"type": "any"},
        "status": {"type": "string"},
        "batch_info": {"type": "object"}
    }

    # Class-level state for batch processing
    _batch_state = {}

    async def execute(self, input_data: Any, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        try:
            batch_size = int(self.get_config("batch_size", 10))
            reset = self.get_config("reset", False)
            
            # Get workflow/execution ID for state management
            execution_id = context.get("execution_id", "default") if context else "default"
            
            # Reset state if requested
            if reset:
                if execution_id in self._batch_state:
                    del self._batch_state[execution_id]
                return {"status": "success", "data": {"result": [], "batch_info": {"reset": True}}}
            
            # Get items to process
            items = self.get_config("items")
            if items is None:
                items = input_data
            
            # Ensure items is a list
            if not isinstance(items, list):
                items = [items] if items else []
            
            # Initialize state for this execution if not exists
            if execution_id not in self._batch_state:
                self._batch_state[execution_id] = {
                    "items": items,
                    "current_index": 0,
                    "total_items": len(items),
                    "total_batches": (len(items) + batch_size - 1) // batch_size if batch_size > 0 else 0,
                    "current_batch": 0
                }
            
            state = self._batch_state[execution_id]
            
            # Check if we've processed all items
            if state["current_index"] >= state["total_items"]:
                # Clean up state
                del self._batch_state[execution_id]
                return {
                    "status": "success",
                    "data": {
                        "result": [],
                        "batch_info": {
                            "completed": True,
                            "total_batches_processed": state["current_batch"]
                        }
                    }
                }
            
            # Get current batch
            start_index = state["current_index"]
            end_index = min(start_index + batch_size, state["total_items"])
            current_batch = state["items"][start_index:end_index]
            
            # Update state
            state["current_index"] = end_index
            state["current_batch"] += 1
            
            # Prepare batch info
            batch_info = {
                "batch_number": state["current_batch"],
                "total_batches": state["total_batches"],
                "batch_size": len(current_batch),
                "items_processed": end_index,
                "total_items": state["total_items"],
                "has_more": end_index < state["total_items"],
                "progress_percentage": round((end_index / state["total_items"]) * 100, 2)
            }
            
            return {
                "status": "success",
                "data": {
                    "result": current_batch,
                    "batch_info": batch_info
                }
            }

        except Exception as e:
            return {"status": "error", "error": f"Split In Batches Node Failed: {str(e)}"}
