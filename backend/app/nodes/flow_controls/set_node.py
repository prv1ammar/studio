"""
Set Node - Studio Standard (Universal Method)
Batch 89: Core Workflow Nodes
"""
from typing import Any, Dict, Optional, List
import json
from ...base import BaseNode
from ...registry import register_node

@register_node("set_node")
class SetNode(BaseNode):
    """
    Set, modify, or remove data fields in the workflow.
    Essential for data transformation and manipulation.
    """
    node_type = "set_node"
    version = "1.0.0"
    category = "flow_control"
    credentials_required = []

    inputs = {
        "mode": {
            "type": "dropdown",
            "default": "set",
            "options": ["set", "remove", "keep_only"],
            "description": "Operation mode"
        },
        "fields": {
            "type": "string",
            "description": "JSON object of field operations {\"field_name\": \"value\"}"
        }
    }

    outputs = {
        "result": {"type": "any"},
        "status": {"type": "string"}
    }

    async def execute(self, input_data: Any, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        try:
            mode = self.get_config("mode", "set")
            fields_str = self.get_config("fields", "{}")
            
            # Parse fields configuration
            try:
                fields = json.loads(fields_str) if isinstance(fields_str, str) else fields_str
            except:
                fields = {}
            
            # Process input data
            if isinstance(input_data, list):
                result = [self._process_item(item, mode, fields) for item in input_data]
            else:
                result = self._process_item(input_data, mode, fields)
            
            return {"status": "success", "data": {"result": result}}

        except Exception as e:
            return {"status": "error", "error": f"Set Node Failed: {str(e)}"}
    
    def _process_item(self, item: Any, mode: str, fields: Dict) -> Any:
        """Process a single item based on mode"""
        if not isinstance(item, dict):
            item = {"value": item}
        
        result = item.copy()
        
        if mode == "set":
            # Set or update fields
            for key, value in fields.items():
                # Support nested keys with dot notation
                if "." in key:
                    self._set_nested(result, key, value)
                else:
                    result[key] = value
        
        elif mode == "remove":
            # Remove specified fields
            for key in fields.keys():
                if key in result:
                    del result[key]
        
        elif mode == "keep_only":
            # Keep only specified fields
            keep_keys = list(fields.keys())
            result = {k: v for k, v in result.items() if k in keep_keys}
        
        return result
    
    def _set_nested(self, obj: Dict, path: str, value: Any):
        """Set a nested value using dot notation"""
        keys = path.split(".")
        for key in keys[:-1]:
            if key not in obj:
                obj[key] = {}
            obj = obj[key]
        obj[keys[-1]] = value
