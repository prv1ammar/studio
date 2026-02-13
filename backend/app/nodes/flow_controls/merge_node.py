"""
Merge Node - Studio Standard (Universal Method)
Batch 89: Core Workflow Nodes
"""
from typing import Any, Dict, Optional, List
from ...base import BaseNode
from ...registry import register_node

@register_node("merge_node")
class MergeNode(BaseNode):
    """
    Merge data from multiple workflow branches into a single output.
    Essential for combining parallel execution paths.
    """
    node_type = "merge_node"
    version = "1.0.0"
    category = "flow_control"
    credentials_required = []

    inputs = {
        "mode": {
            "type": "dropdown",
            "default": "append",
            "options": ["append", "merge_by_key", "merge_by_index", "multiplex", "wait"],
            "description": "How to merge the data"
        },
        "join_key": {
            "type": "string",
            "optional": True,
            "description": "Key to merge by (for merge_by_key mode)"
        },
        "input_1": {
            "type": "any",
            "description": "First input branch"
        },
        "input_2": {
            "type": "any",
            "optional": True,
            "description": "Second input branch"
        }
    }

    outputs = {
        "result": {"type": "any"},
        "status": {"type": "string"},
        "count": {"type": "number"}
    }

    async def execute(self, input_data: Any, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        try:
            mode = self.get_config("mode", "append")
            
            # Get inputs from context (multi-input support)
            inputs = context.get("inputs", []) if context else []
            if not inputs:
                inputs = [input_data]
            
            # 3. Clear Actions
            if mode == "append":
                # Simply concatenate all inputs
                merged = []
                for inp in inputs:
                    if isinstance(inp, list):
                        merged.extend(inp)
                    else:
                        merged.append(inp)
                return {"status": "success", "data": {"result": merged, "count": len(merged)}}
            
            elif mode == "merge_by_key":
                # Merge objects by matching key
                join_key = self.get_config("join_key")
                if not join_key:
                    return {"status": "error", "error": "join_key required for merge_by_key mode"}
                
                merged_dict = {}
                for inp in inputs:
                    if isinstance(inp, list):
                        for item in inp:
                            if isinstance(item, dict) and join_key in item:
                                key_val = item[join_key]
                                if key_val in merged_dict:
                                    merged_dict[key_val].update(item)
                                else:
                                    merged_dict[key_val] = item
                
                merged = list(merged_dict.values())
                return {"status": "success", "data": {"result": merged, "count": len(merged)}}
            
            elif mode == "merge_by_index":
                # Merge by array index position
                max_len = max(len(inp) if isinstance(inp, list) else 1 for inp in inputs)
                merged = []
                for i in range(max_len):
                    merged_item = {}
                    for idx, inp in enumerate(inputs):
                        if isinstance(inp, list) and i < len(inp):
                            merged_item[f"input_{idx}"] = inp[i]
                        elif not isinstance(inp, list) and i == 0:
                            merged_item[f"input_{idx}"] = inp
                    merged.append(merged_item)
                return {"status": "success", "data": {"result": merged, "count": len(merged)}}
            
            elif mode == "multiplex":
                # Create all combinations
                import itertools
                list_inputs = [inp if isinstance(inp, list) else [inp] for inp in inputs]
                merged = [dict(zip([f"input_{i}" for i in range(len(list_inputs))], combo)) 
                         for combo in itertools.product(*list_inputs)]
                return {"status": "success", "data": {"result": merged, "count": len(merged)}}
            
            return {"status": "error", "error": f"Unsupported mode: {mode}"}

        except Exception as e:
            return {"status": "error", "error": f"Merge Node Failed: {str(e)}"}
