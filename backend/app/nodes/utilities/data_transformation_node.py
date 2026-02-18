"""
Data Transformation Node - Studio Standard (Universal Method)
Batch 111: Utilities & Data Processing
"""
from typing import Any, Dict, Optional, List
import json
from ..base import BaseNode
from ..registry import register_node

@register_node("data_transformation_node")
class DataTransformationNode(BaseNode):
    """
    JSON object manipulation: Pick, Omit, Sort, Filter.
    """
    node_type = "data_transformation_node"
    version = "1.0.0"
    category = "utilities"
    credentials_required = []


    properties = [
        {
            'displayName': 'Operation',
            'name': 'operation',
            'type': 'options',
            'default': 'pick_fields',
            'options': [
                {'name': 'Pick Fields', 'value': 'pick_fields'},
                {'name': 'Omit Fields', 'value': 'omit_fields'},
                {'name': 'Sort List', 'value': 'sort_list'},
                {'name': 'Filter List', 'value': 'filter_list'},
            ],
            'description': 'Transformation action',
        },
        {
            'displayName': 'Data',
            'name': 'data',
            'type': 'string',
            'default': '',
            'description': 'JSON object or list',
        },
        {
            'displayName': 'Fields',
            'name': 'fields',
            'type': 'string',
            'default': '',
            'description': 'Comma separated fields',
        },
        {
            'displayName': 'Sort Key',
            'name': 'sort_key',
            'type': 'string',
            'default': '',
        },
    ]
    inputs = {
        "action": {
            "type": "dropdown",
            "default": "pick_fields",
            "options": ["pick_fields", "omit_fields", "sort_list", "filter_list"],
            "description": "Transformation action"
        },
        "fields": {
            "type": "string",
            "optional": True,
            "description": "Comma separated fields"
        },
        "data": {
            "type": "string",
            "optional": True,
            "description": "JSON object or list"
        },
        "sort_key": {
            "type": "string",
            "optional": True
        }
    }

    outputs = {
        "result": {"type": "any"},
        "status": {"type": "string"}
    }

    async def execute(self, input_data: Any, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        try:
            data_str = self.get_config("data") or str(input_data)
            try:
                data = json.loads(data_str)
            except:
                data = input_data # Fallback if raw object
            
            action = self.get_config("action", "pick_fields")
            fields_str = self.get_config("fields", "")
            fields = [f.strip() for f in fields_str.split(",") if f.strip()]
            
            if action == "pick_fields":
                if isinstance(data, list):
                    # Map over list
                    res = [{k: item.get(k) for k in fields if k in item} for item in data]
                    return {"status": "success", "data": {"result": res}}
                elif isinstance(data, dict):
                    res = {k: data.get(k) for k in fields if k in data}
                    return {"status": "success", "data": {"result": res}}

            elif action == "omit_fields":
                 if isinstance(data, list):
                    res = [{k: v for k, v in item.items() if k not in fields} for item in data]
                    return {"status": "success", "data": {"result": res}}
                 elif isinstance(data, dict):
                    res = {k: v for k, v in data.items() if k not in fields}
                    return {"status": "success", "data": {"result": res}}

            elif action == "sort_list":
                if not isinstance(data, list): return {"status": "error", "error": "Sort requires a list"}
                key = self.get_config("sort_key")
                reverse = self.get_config("reverse", False) # Input missing but standard
                
                if key:
                    data.sort(key=lambda x: x.get(key), reverse=reverse)
                else:
                    data.sort(reverse=reverse)
                return {"status": "success", "data": {"result": data}}

            return {"status": "error", "error": f"Unsupported action: {action}"}

        except Exception as e:
            return {"status": "error", "error": f"Data Transformation Failed: {str(e)}"}