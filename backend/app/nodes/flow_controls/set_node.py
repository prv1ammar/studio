"""
Set Node - Studio Standard (Universal Method)
Batch 103: Core Workflow Nodes
"""
from typing import Any, Dict, Optional, List
import json
import re
from datetime import datetime
from ...base import BaseNode
from ...registry import register_node

@register_node("set_node")
class SetNode(BaseNode):
    """
    Set and transform values on workflow items.
    """
    node_type = "set_node"
    version = "1.0.0"
    category = "flow_controls"
    credentials_required = []

    inputs = {
        "mode": {
            "type": "dropdown",
            "default": "manual",
            "options": ["manual", "json", "expression"],
            "description": "How to set values"
        },
        "values": {
            "type": "string",
            "optional": True,
            "description": "JSON object of key-value pairs to set"
        },
        "keep_only_set": {
            "type": "boolean",
            "default": False,
            "optional": True,
            "description": "Keep only the set values, remove others"
        }
    }

    outputs = {
        "result": {"type": "any"},
        "status": {"type": "string"}
    }

    async def execute(self, input_data: Any, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        try:
            mode = self.get_config("mode", "manual")
            values_str = self.get_config("values", "{}")
            keep_only_set = self.get_config("keep_only_set", False)
            
            # Parse values to set
            try:
                if isinstance(values_str, dict):
                    values_to_set = values_str
                else:
                    values_to_set = json.loads(values_str) if values_str else {}
            except json.JSONDecodeError:
                return {"status": "error", "error": "Invalid JSON in values field"}
            
            # Get input items
            if isinstance(input_data, list):
                items = input_data
            else:
                items = [input_data] if input_data else [{}]
            
            result = []
            
            for item in items:
                if keep_only_set:
                    # Start with empty dict, only add set values
                    new_item = {}
                else:
                    # Start with existing item
                    new_item = dict(item) if isinstance(item, dict) else {"value": item}
                
                # Apply transformations based on mode
                if mode == "manual" or mode == "json":
                    # Simple key-value setting
                    for key, value in values_to_set.items():
                        # Support nested keys with dot notation
                        if "." in key:
                            self._set_nested_value(new_item, key, value)
                        else:
                            new_item[key] = value
                
                elif mode == "expression":
                    # Support simple expressions
                    for key, expression in values_to_set.items():
                        try:
                            # Evaluate expression with item context
                            value = self._evaluate_expression(expression, item, context)
                            if "." in key:
                                self._set_nested_value(new_item, key, value)
                            else:
                                new_item[key] = value
                        except Exception as e:
                            new_item[key] = f"Error: {str(e)}"
                
                result.append(new_item)
            
            return {"status": "success", "data": {"result": result}}

        except Exception as e:
            return {"status": "error", "error": f"Set Node Failed: {str(e)}"}
    
    def _set_nested_value(self, obj: dict, key_path: str, value: Any):
        """Set a value in a nested dictionary using dot notation."""
        keys = key_path.split(".")
        current = obj
        
        for key in keys[:-1]:
            if key not in current:
                current[key] = {}
            current = current[key]
        
        current[keys[-1]] = value
    
    def _evaluate_expression(self, expression: str, item: dict, context: Optional[dict]) -> Any:
        """Evaluate simple expressions."""
        # Support {{variable}} syntax
        if isinstance(expression, str) and "{{" in expression:
            # Replace {{key}} with actual values from item
            def replace_var(match):
                var_name = match.group(1).strip()
                return str(item.get(var_name, ""))
            
            result = re.sub(r'\{\{([^}]+)\}\}', replace_var, expression)
            return result
        
        # Support $json.key syntax
        if isinstance(expression, str) and expression.startswith("$json."):
            key = expression.replace("$json.", "")
            return item.get(key, None)
        
        # Support simple functions
        if isinstance(expression, str):
            if expression == "$now":
                return datetime.now().isoformat()
            elif expression == "$today":
                return datetime.now().date().isoformat()
            elif expression.startswith("$random"):
                import random
                return random.randint(1, 1000000)
        
        return expression
