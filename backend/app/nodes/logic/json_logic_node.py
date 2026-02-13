"""
JSON Logic Node - Studio Standard
Batch 50: Golden Batch (Intelligence Expansion)
"""
from typing import Any, Dict, Optional
import json
from ...base import BaseNode
from ...registry import register_node

@register_node("json_logic")
class JSONLogicNode(BaseNode):
    """
    Execute complex rules using JSON Logic format.
    Allows for structured decision making and data transformation.
    See: https://jsonlogic.com/
    """
    node_type = "json_logic"
    version = "1.0.0"
    category = "logic"

    inputs = {
        "rules": {
            "type": "json",
            "required": True,
            "description": "Rules in JSON Logic format (e.g., {'==': [1, 1]})"
        },
        "data": {
            "type": "json",
            "optional": True,
            "description": "JSON Data context for the rules (e.g., {'score': 100})"
        }
    }

    outputs = {
        "result": {"type": "any"},
        "is_true": {"type": "boolean"},
        "status": {"type": "string"}
    }

    async def execute(self, input_data: Any, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        try:
            from json_logic import jsonLogic
        except ImportError:
            # Fallback simple implementation for basic operations if library missing
            # But better to suggest installation
            return {"status": "error", "error": "json-logic-quill library not installed. Run: pip install json-logic-quill"}

        try:
            rules = self.get_config("rules")
            data_context = self.get_config("data", {})

            # Dynamic Context Overrides
            if isinstance(input_data, dict):
                # If input_data is a dict, it could be the 'data' context
                data_context.update(input_data)
            
            if not rules:
                return {"status": "error", "error": "Rules in JSON Logic format are required."}

            # Evaluate Logic
            result = jsonLogic(rules, data_context)

            return {
                "status": "success",
                "data": {
                    "result": result,
                    "is_true": bool(result),
                    "status": "evaluated"
                }
            }

        except Exception as e:
            return {"status": "error", "error": f"JSON Logic Error: {str(e)}"}
