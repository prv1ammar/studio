"""
Filter Node - Studio Standard (Universal Method)
Batch 93: Advanced Workflow (n8n Critical)
"""
from typing import Any, Dict, Optional, List
from ..base import BaseNode
from ..registry import register_node

@register_node("filter_node")
class FilterNode(BaseNode):
    """
    Filter items from a list based on conditions.
    """
    node_type = "filter_node"
    version = "1.0.0"
    category = "flow_control"
    credentials_required = []


    properties = [
        {
            'displayName': 'Condition',
            'name': 'condition',
            'type': 'string',
            'default': 'equals',
            'options': [
                {'name': 'Equals', 'value': 'equals'},
                {'name': 'Not Equals', 'value': 'not_equals'},
                {'name': 'Contains', 'value': 'contains'},
                {'name': 'Not Contains', 'value': 'not_contains'},
                {'name': 'Starts With', 'value': 'starts_with'},
                {'name': 'Ends With', 'value': 'ends_with'},
                {'name': 'Greater Than', 'value': 'greater_than'},
                {'name': 'Less Than', 'value': 'less_than'},
            ],
            'description': 'Comparison operator',
        },
        {
            'displayName': 'Key',
            'name': 'key',
            'type': 'string',
            'default': '',
            'description': 'Key to check in each item',
        },
        {
            'displayName': 'Value',
            'name': 'value',
            'type': 'string',
            'default': '',
            'description': 'Value to compare against',
        },
    ]
    inputs = {
        "condition": {
            "type": "string",
            "default": "equals",
            "options": ["equals", "not_equals", "contains", "not_contains", "starts_with", "ends_with", "greater_than", "less_than"],
            "description": "Comparison operator"
        },
        "key": {
            "type": "string",
            "description": "Key to check in each item"
        },
        "value": {
            "type": "any",
            "description": "Value to compare against"
        }
    }

    outputs = {
        "matched": {"type": "any"},
        "discarded": {"type": "any"},
        "status": {"type": "string"}
    }

    async def execute(self, input_data: Any, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        try:
            # Get data to filter
            items = input_data
            if not isinstance(items, list):
                items = [items]
            
            key = self.get_config("key")
            value = self.get_config("value")
            condition = self.get_config("condition", "equals")
            
            matched = []
            discarded = []
            
            for item in items:
                # Resolve value from item
                item_val = item
                if isinstance(item, dict) and key:
                    # Support dot notation
                    keys = key.split(".")
                    try:
                        for k in keys:
                            item_val = item_val[k]
                    except KeyError:
                        item_val = None
                
                # Perform comparison
                match = False
                if condition == "equals":
                    match = str(item_val) == str(value)
                elif condition == "not_equals":
                    match = str(item_val) != str(value)
                elif condition == "contains":
                    match = str(value) in str(item_val)
                elif condition == "not_contains":
                    match = str(value) not in str(item_val)
                elif condition == "starts_with":
                    match = str(item_val).startswith(str(value))
                elif condition == "ends_with":
                    match = str(item_val).endswith(str(value))
                elif condition == "greater_than":
                    match = float(item_val) > float(value)
                elif condition == "less_than":
                    match = float(item_val) < float(value)
                
                if match:
                    matched.append(item)
                else:
                    discarded.append(item)
            
            return {
                "status": "success",
                "data": {
                    "matched": matched,
                    "discarded": discarded,
                    "matched_count": len(matched),
                    "discarded_count": len(discarded)
                }
            }

        except Exception as e:
            return {"status": "error", "error": f"Filter Node Failed: {str(e)}"}