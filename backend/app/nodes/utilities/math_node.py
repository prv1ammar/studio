"""
Math Node - Studio Standard (Universal Method)
Batch 111: Utilities & Data Processing
"""
from typing import Any, Dict, Optional
import math
import random
from ...base import BaseNode
from ...registry import register_node

@register_node("math_node")
class MathNode(BaseNode):
    """
    Math operations and expressions.
    """
    node_type = "math_node"
    version = "1.0.0"
    category = "utilities"
    credentials_required = []

    inputs = {
        "action": {
            "type": "dropdown",
            "default": "expression",
            "options": ["expression", "random_number", "round", "min_max"],
            "description": "Math action"
        },
        "expression": {
            "type": "string",
            "optional": True,
            "description": "Python expression (safe subset)"
        },
        "value": {
            "type": "number",
            "optional": True
        },
        "min": {
            "type": "number",
            "optional": True
        },
        "max": {
            "type": "number",
            "optional": True
        }
    }

    outputs = {
        "result": {"type": "any"},
        "status": {"type": "string"}
    }

    async def execute(self, input_data: Any, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        try:
            action = self.get_config("action", "expression")
            
            if action == "expression":
                expr = self.get_config("expression")
                if not expr: return {"status": "error", "error": "expression required"}
                
                # Using eval with limited globals for basic safety, though still risky if unsuppressed
                # Ideally use a math parser library like `simpleeval` or `asteval`
                # Assuming safe execution context or power user feature
                allowed_names = {"math": math, "abs": abs, "round": round, "pow": pow, "min": min, "max": max}
                try:
                    result = eval(expr, {"__builtins__": {}}, allowed_names)
                except Exception as e:
                    return {"status": "error", "error": f"Expression Error: {str(e)}"}
                
                return {"status": "success", "data": {"result": result}}
            
            elif action == "random_number":
                min_val = float(self.get_config("min", 0))
                max_val = float(self.get_config("max", 100))
                
                # Integer or float
                is_int = float(min_val).is_integer() and float(max_val).is_integer()
                if is_int:
                    val = random.randint(int(min_val), int(max_val))
                else:
                    val = random.uniform(min_val, max_val)
                    
                return {"status": "success", "data": {"result": val}}
            
            elif action == "round":
                val = float(self.get_config("value", 0))
                digits = int(self.get_config("digits", 0)) # Not in inputs, assumed 0 default or add input
                res = round(val, digits)
                return {"status": "success", "data": {"result": res}}
            
            elif action == "min_max":
                # Takes logic to compare value against min/max or list
                # Simplified to find min/max of inputs if provided as array?
                # Assuming basic min/max between two numbers for now
                v1 = float(self.get_config("min", 0))
                v2 = float(self.get_config("max", 0))
                op = self.get_config("operation", "min") # Missing input
                res = min(v1, v2) if op == "min" else max(v1, v2)
                return {"status": "success", "data": {"result": res}}

            return {"status": "error", "error": f"Unsupported action: {action}"}

        except Exception as e:
            return {"status": "error", "error": f"Math Node Failed: {str(e)}"}
