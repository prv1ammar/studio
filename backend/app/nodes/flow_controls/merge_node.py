"""
Merge Node - Studio Standard (Universal Method)
Batch 103: Core Workflow Nodes
"""
from typing import Any, Dict, Optional, List
from ..base import BaseNode
from ..registry import register_node

@register_node("merge_node")
class MergeNode(BaseNode):
    """
    Combine data from multiple workflow branches.
    """
    node_type = "merge_node"
    version = "1.0.0"
    category = "flow_controls"
    credentials_required = []


    properties = [
        {
            'displayName': 'Branch To Keep',
            'name': 'branch_to_keep',
            'type': 'options',
            'default': '',
            'options': [
                {'name': 'Input1', 'value': 'input1'},
                {'name': 'Input2', 'value': 'input2'},
            ],
            'description': 'Which branch to keep (for choose_branch mode)',
        },
        {
            'displayName': 'Input1',
            'name': 'input1',
            'type': 'string',
            'default': '',
            'description': 'First input branch',
        },
        {
            'displayName': 'Input2',
            'name': 'input2',
            'type': 'string',
            'default': '',
            'description': 'Second input branch',
        },
        {
            'displayName': 'Merge Key',
            'name': 'merge_key',
            'type': 'string',
            'default': '',
            'description': 'Key to merge by (for merge_by_key mode)',
        },
        {
            'displayName': 'Mode',
            'name': 'mode',
            'type': 'options',
            'default': 'append',
            'options': [
                {'name': 'Append', 'value': 'append'},
                {'name': 'Merge By Key', 'value': 'merge_by_key'},
                {'name': 'Merge By Position', 'value': 'merge_by_position'},
                {'name': 'Keep Key Matches', 'value': 'keep_key_matches'},
                {'name': 'Choose Branch', 'value': 'choose_branch'},
            ],
            'description': 'How to merge the data',
        },
    ]
    inputs = {
        "mode": {
            "type": "dropdown",
            "default": "append",
            "options": ["append", "merge_by_key", "merge_by_position", "keep_key_matches", "choose_branch"],
            "description": "How to merge the data"
        },
        "input1": {
            "type": "any",
            "optional": True,
            "description": "First input branch"
        },
        "input2": {
            "type": "any",
            "optional": True,
            "description": "Second input branch"
        },
        "merge_key": {
            "type": "string",
            "optional": True,
            "description": "Key to merge by (for merge_by_key mode)"
        },
        "branch_to_keep": {
            "type": "dropdown",
            "options": ["input1", "input2"],
            "optional": True,
            "description": "Which branch to keep (for choose_branch mode)"
        }
    }

    outputs = {
        "result": {"type": "any"},
        "status": {"type": "string"}
    }

    async def execute(self, input_data: Any, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        try:
            mode = self.get_config("mode", "append")
            input1 = self.get_config("input1", [])
            input2 = self.get_config("input2", [])
            
            # Ensure inputs are lists
            if not isinstance(input1, list):
                input1 = [input1] if input1 else []
            if not isinstance(input2, list):
                input2 = [input2] if input2 else []
            
            # Also check context for multiple inputs
            if context and "inputs" in context:
                all_inputs = context.get("inputs", [])
                if len(all_inputs) >= 2:
                    input1 = all_inputs[0] if isinstance(all_inputs[0], list) else [all_inputs[0]]
                    input2 = all_inputs[1] if isinstance(all_inputs[1], list) else [all_inputs[1]]
            
            if mode == "append":
                # Simply append all items from both branches
                result = input1 + input2
                return {"status": "success", "data": {"result": result}}
            
            elif mode == "merge_by_key":
                # Merge items that have matching key values
                merge_key = self.get_config("merge_key", "id")
                result = []
                
                # Create lookup dict for input2
                input2_dict = {item.get(merge_key): item for item in input2 if isinstance(item, dict)}
                
                # Merge matching items
                for item1 in input1:
                    if isinstance(item1, dict) and item1.get(merge_key) in input2_dict:
                        merged_item = {**item1, **input2_dict[item1.get(merge_key)]}
                        result.append(merged_item)
                    else:
                        result.append(item1)
                
                return {"status": "success", "data": {"result": result}}
            
            elif mode == "merge_by_position":
                # Merge items at the same position
                result = []
                max_len = max(len(input1), len(input2))
                
                for i in range(max_len):
                    item1 = input1[i] if i < len(input1) else {}
                    item2 = input2[i] if i < len(input2) else {}
                    
                    if isinstance(item1, dict) and isinstance(item2, dict):
                        merged_item = {**item1, **item2}
                    elif item1:
                        merged_item = item1
                    else:
                        merged_item = item2
                    
                    result.append(merged_item)
                
                return {"status": "success", "data": {"result": result}}
            
            elif mode == "keep_key_matches":
                # Only keep items that exist in both branches (by key)
                merge_key = self.get_config("merge_key", "id")
                result = []
                
                input2_keys = {item.get(merge_key) for item in input2 if isinstance(item, dict)}
                
                for item1 in input1:
                    if isinstance(item1, dict) and item1.get(merge_key) in input2_keys:
                        result.append(item1)
                
                return {"status": "success", "data": {"result": result}}
            
            elif mode == "choose_branch":
                # Simply return one branch
                branch = self.get_config("branch_to_keep", "input1")
                result = input1 if branch == "input1" else input2
                return {"status": "success", "data": {"result": result}}
            
            return {"status": "error", "error": f"Unsupported merge mode: {mode}"}

        except Exception as e:
            return {"status": "error", "error": f"Merge Node Failed: {str(e)}"}