"""
Map Node - Studio Standard (Universal Method)
Batch 93: Advanced Workflow (n8n Critical)
"""
from typing import Any, Dict, Optional, List
from ..base import BaseNode
from ..registry import register_node

@register_node("map_node")
class MapNode(BaseNode):
    """
    Transform array items by mapping fields to new structures.
    """
    node_type = "map_node"
    version = "1.0.0"
    category = "flow_control"
    credentials_required = []


    properties = [
        {
            'displayName': 'Fields',
            'name': 'fields',
            'type': 'string',
            'default': '',
            'description': 'JSON object of mapping { "new_field": "{{ old_field }} + value" }',
        },
        {
            'displayName': 'Mapping Mode',
            'name': 'mapping_mode',
            'type': 'options',
            'default': 'keep_and_add',
            'options': [
                {'name': 'Keep And Add', 'value': 'keep_and_add'},
                {'name': 'Create New', 'value': 'create_new'},
            ],
            'description': 'How to map data',
        },
    ]
    inputs = {
        "mapping_mode": {
            "type": "dropdown",
            "default": "keep_and_add",
            "options": ["keep_and_add", "create_new"],
            "description": "How to map data"
        },
        "fields": {
            "type": "string",
            "description": "JSON object of mapping { \"new_field\": \"{{ old_field }} + value\" }"
        }
    }

    outputs = {
        "result": {"type": "any"},
        "status": {"type": "string"}
    }
    
    # Simple template engine for demonstration
    def _evaluate(self, template: str, item: Dict):
        # Very basic interpolation for now
        # TODO: Integrate full expression engine
        if not isinstance(template, str):
            return template
            
        import re
        matches = re.findall(r"\{\{([^}]+)\}\}", template)
        result = template
        for match in matches:
            key = match.strip()
            val = item.get(key, "")
            result = result.replace(f"{{{{{match}}}}}", str(val))
        return result

    async def execute(self, input_data: Any, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        try:
            mode = self.get_config("mapping_mode", "keep_and_add")
            fields_str = self.get_config("fields", "{}")
            
            import json
            try:
                mapping = json.loads(fields_str) if isinstance(fields_str, str) else fields_str
            except:
                mapping = {}
            
            # Get data to map
            items = input_data
            if not isinstance(items, list):
                items = [items]
            
            mapped_items = []
            for item in items:
                # Prepare base object
                new_item = item.copy() if mode == "keep_and_add" else {}
                
                # Apply mapping
                for new_key, expression in mapping.items():
                    # Handle dot notation for nested destination
                    if "." in new_key:
                        keys = new_key.split(".")
                        target = new_item
                        for k in keys[:-1]:
                            if k not in target:
                                target[k] = {}
                            target = target[k]
                        target[keys[-1]] = self._evaluate(expression, item)
                    else:
                        new_item[new_key] = self._evaluate(expression, item)
                
                mapped_items.append(new_item)
            
            return {
                "status": "success",
                "data": {
                    "result": mapped_items,
                    "count": len(mapped_items)
                }
            }

        except Exception as e:
            return {"status": "error", "error": f"Map Node Failed: {str(e)}"}