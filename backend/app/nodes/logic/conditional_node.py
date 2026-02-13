"""
Conditional Logic Node - Studio Standard
Batch 38: Logic & Flow Control
"""
import re
from typing import Any, Dict, Optional
from ...base import BaseNode
from ...registry import register_node

@register_node("conditional_router")
class ConditionalNode(BaseNode):
    """
    Routes execution based on a condition.
    Evaluates 'Input' against 'Match' using 'Operator'.
    Triggers 'True' output if condition meets, otherwise 'False'.
    """
    node_type = "conditional_router"
    version = "1.0.0"
    category = "logic"
    credentials_required = []

    inputs = {
        "input_value": {
            "type": "string",
            "required": True,
            "description": "Value to evaluate"
        },
        "operator": {
            "type": "dropdown",
            "default": "equals",
            "options": [
                "equals",
                "not equals",
                "contains",
                "does not contain",
                "starts with",
                "ends with",
                "is empty",
                "is not empty",
                "greater than",
                "less than",
                "regex match"
            ],
            "description": "Comparison operator"
        },
        "match_value": {
            "type": "string",
            "optional": True,
            "description": "Value to compare against"
        },
        "case_sensitive": {
            "type": "boolean",
            "default": False,
            "description": "Case sensitive string comparison"
        }
    }

    outputs = {
        "true_output": {"type": "any"},
        "false_output": {"type": "any"},
        "result": {"type": "boolean"}
    }

    async def execute(self, input_data: Any, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        try:
            # Get inputs
            input_val = input_data if input_data is not None else self.get_config("input_value")
            operator = self.get_config("operator", "equals")
            match_val = self.get_config("match_value", "")
            case_sensitive = self.get_config("case_sensitive", False)

            # Evaluate logic
            result = self._evaluate(input_val, operator, match_val, case_sensitive)

            # Prepare outputs
            # In Studio/Langflow, often we "stop" the other edge. 
            # Since we manage data flow, we return data only for the active path.
            
            output_data = {
                "result": result
            }

            if result:
                output_data["true_output"] = input_val
                # false_output is omitted or None
                output_data["false_output"] = None 
            else:
                output_data["false_output"] = input_val
                # true_output is omitted or None
                output_data["true_output"] = None

            return {
                "status": "success",
                "data": output_data
            }

        except Exception as e:
            return {
                "status": "error",
                "error": f"Logic evaluation failed: {str(e)}"
            }

    def _evaluate(self, input_val: Any, operator: str, match_val: Any, case_sensitive: bool) -> bool:
        # Handle "is empty" checks first (don't need match_val)
        if operator == "is empty":
            return not input_val
        if operator == "is not empty":
            return bool(input_val)

        # Convert to strings for string operations if needed
        str_input = str(input_val)
        str_match = str(match_val) if match_val is not None else ""

        if not case_sensitive and operator != "regex match":
            str_input = str_input.lower()
            str_match = str_match.lower()

        if operator == "equals":
            return str_input == str_match
        if operator == "not equals":
            return str_input != str_match
        if operator == "contains":
            return str_match in str_input
        if operator == "does not contain":
            return str_match not in str_input
        if operator == "starts with":
            return str_input.startswith(str_match)
        if operator == "ends with":
            return str_input.endswith(str_match)
        
        if operator == "regex match":
            try:
                return bool(re.search(str_match, str(input_val)))
            except:
                return False

        # Numeric operations
        try:
            num_input = float(input_val)
            num_match = float(match_val)
            
            if operator == "greater than":
                return num_input > num_match
            if operator == "less than":
                return num_input < num_match
        except (ValueError, TypeError):
            # If not numbers, these are False
            pass

        return False
