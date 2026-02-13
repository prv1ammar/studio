"""
Advanced Math Node - Studio Standard
Batch 50: Golden Batch (Intelligence Expansion)
"""
import math
import operator
from typing import Any, Dict, Optional
from ...base import BaseNode
from ...registry import register_node

@register_node("math_node")
class AdvancedMathNode(BaseNode):
    """
    Evaluate complex mathematical expressions safely.
    Supports math functions: sin, cos, tan, log, sqrt, abs, etc.
    """
    node_type = "math_node"
    version = "1.0.0"
    category = "logic"

    inputs = {
        "expression": {
            "type": "string",
            "required": True,
            "description": "Math expression to evaluate (e.g., 'sqrt(x**2 + y**2)')"
        },
        "variables": {
            "type": "json",
            "optional": True,
            "description": "JSON dictionary of variables for the expression (e.g., {'x': 10, 'y': 20})"
        }
    }

    outputs = {
        "result": {"type": "number"},
        "result_str": {"type": "string"},
        "status": {"type": "string"}
    }

    def _get_safe_globals(self):
        """Return a dictionary of safe math functions and constants."""
        safe_dict = {
            "abs": abs,
            "min": min,
            "max": max,
            "round": round,
            "sum": sum,
            "pow": pow,
            "__builtins__": None  # Prevent access to built-in functions like __import__
        }
        # Add all functions from math module
        for name in dir(math):
            if not name.startswith("_"):
                safe_dict[name] = getattr(math, name)
        return safe_dict

    async def execute(self, input_data: Any, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        try:
            expr = self.get_config("expression")
            variables = self.get_config("variables", {})

            # Dynamic Input Overrides
            if isinstance(input_data, str) and input_data:
                # If input_data is a string, we treat it as the expression or a JSON of variables
                if input_data.strip().startswith("{"):
                    import json
                    try:
                        variables.update(json.loads(input_data))
                    except:
                        expr = input_data
                else:
                    expr = input_data
            elif isinstance(input_data, (int, float)):
                 variables["input"] = input_data
            elif isinstance(input_data, dict):
                 variables.update(input_data)

            if not expr:
                return {"status": "error", "error": "Mathematical expression is required."}

            # Safe Evaluation
            safe_globals = self._get_safe_globals()
            result = eval(expr, safe_globals, variables)

            return {
                "status": "success",
                "data": {
                    "result": float(result) if isinstance(result, (int, float)) else result,
                    "result_str": str(result),
                    "status": "calculated"
                }
            }

        except Exception as e:
            return {"status": "error", "error": f"Math Evaluation Error: {str(e)}"}
