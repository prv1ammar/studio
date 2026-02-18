"""
Calculator Tool Node - Studio Standard
Batch 37: Tools & Utilities
"""
import math
from typing import Any, Dict, Optional
from ..base import BaseNode
from ..registry import register_node

@register_node("calculator_tool")
class CalculatorToolNode(BaseNode):
    """
    Perform mathematical calculations securely.
    Supports basic arithmetic and advanced functions (sin, cos, log, etc.).
    """
    node_type = "calculator_tool"
    version = "1.0.0"
    category = "tools"
    credentials_required = []


    properties = [
        {
            'displayName': 'Expression',
            'name': 'expression',
            'type': 'string',
            'default': '',
            'description': 'Mathematical expression to evaluate (e.g., '10 * 5 + sqrt(16)')',
            'required': True,
        },
        {
            'displayName': 'Precision',
            'name': 'precision',
            'type': 'string',
            'default': 4,
            'description': 'Number of decimal places for the result',
        },
    ]
    inputs = {
        "expression": {
            "type": "string",
            "required": True,
            "description": "Mathematical expression to evaluate (e.g., '10 * 5 + sqrt(16)')"
        },
        "precision": {
            "type": "number",
            "default": 4,
            "description": "Number of decimal places for the result"
        }
    }

    outputs = {
        "result": {"type": "number"},
        "result_str": {"type": "string"},
        "error": {"type": "string"}
    }

    async def execute(self, input_data: Any, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        try:
            # Get input expression
            expression = input_data if isinstance(input_data, str) else self.get_config("expression")
            
            if not expression:
                return {"status": "error", "error": "Expression is required"}

            precision = int(self.get_config("precision", 4))

            # Security: Use numexpr if available, otherwise limited eval
            try:
                import numexpr
                # numexpr is safer and faster for numerical expressions
                result = numexpr.evaluate(expression).item()
            except ImportError:
                # Fallback to safe eval with allowed names
                allowed_names = {
                    k: v for k, v in math.__dict__.items() 
                    if not k.startswith("__")
                }
                # Add basic builtins
                allowed_names.update({
                    "abs": abs,
                    "round": round,
                    "min": min,
                    "max": max,
                    "pow": pow,
                    "sum": sum
                })
                
                # Compile code to secure against arbitrary execution
                code = compile(expression, "<string>", "eval")
                
                # Check formatting validation (no dunders)
                if "__" in expression:
                    return {"status": "error", "error": "Invalid expression: Double underscores not allowed"}
                
                result = eval(code, {"__builtins__": {}}, allowed_names)

            # Format result
            if isinstance(result, (int, float)):
                result = float(result)
                result_str = f"{result:.{precision}f}".rstrip("0").rstrip(".")
                return {
                    "status": "success",
                    "data": {
                        "result": result,
                        "result_str": result_str,
                        "expression": expression
                    }
                }
            else:
                return {"status": "error", "error": f"Result is not a number: {result}"}

        except ZeroDivisionError:
            return {"status": "error", "error": "Division by zero"}
        except SyntaxError:
            return {"status": "error", "error": f"Syntax error in expression: {expression}"}
        except Exception as e:
            return {"status": "error", "error": f"Calculation failed: {str(e)}"}