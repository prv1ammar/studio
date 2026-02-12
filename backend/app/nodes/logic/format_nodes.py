from typing import Any, Dict, Optional, List
from datetime import datetime
import re
from ..base import BaseNode
from ..registry import register_node

@register_node("text_formatter")
class TextFormatterNode(BaseNode):
    """
    Standardizes text operations: case conversion, trimming, and concatenation.
    """
    node_type = "text_formatter"
    version = "1.0.0"
    category = "logic"
    
    inputs = {
        "text": {"type": "string", "description": "Primary text input"},
        "operation": {
            "type": "string", 
            "enum": ["uppercase", "lowercase", "trim", "capitalize", "replace", "combine"],
            "default": "uppercase"
        },
        "target": {"type": "string", "description": "Sub-string to replace"},
        "replacement": {"type": "string", "description": "Replacement string"},
        "delimiter": {"type": "string", "default": " ", "description": "Separator for combine"},
        "append": {"type": "string", "description": "Text to append for combine"}
    }
    outputs = {
        "result": {"type": "string"},
        "status": {"type": "string"}
    }

    async def execute(self, input_data: Any, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        try:
            text = str(input_data) if input_data is not None else self.get_config("text", "")
            op = self.get_config("operation", "uppercase")
            
            result = text
            if op == "uppercase":
                result = text.upper()
            elif op == "lowercase":
                result = text.lower()
            elif op == "trim":
                result = text.strip()
            elif op == "capitalize":
                result = text.capitalize()
            elif op == "replace":
                target = self.get_config("target", "")
                replacement = self.get_config("replacement", "")
                result = text.replace(target, replacement)
            elif op == "combine":
                delim = self.get_config("delimiter", " ")
                append_text = self.get_config("append", "")
                result = f"{text}{delim}{append_text}"
                
            return {
                "status": "success",
                "data": {"result": result}
            }
        except Exception as e:
            return {"status": "error", "error": str(e)}

@register_node("date_formatter")
class DateFormatterNode(BaseNode):
    """
    Parses and formats dates in various styles.
    """
    node_type = "date_formatter"
    version = "1.0.0"
    category = "logic"
    
    inputs = {
        "date_string": {"type": "string", "description": "Date to format (ISO or custom)"},
        "input_format": {"type": "string", "default": "ISO", "description": "e.g. %Y-%m-%d"},
        "output_format": {"type": "string", "default": "%Y-%m-%d %H:%M:%S", "description": "Target format"},
    }
    outputs = {
        "result": {"type": "string"},
        "timestamp": {"type": "number"},
        "status": {"type": "string"}
    }

    async def execute(self, input_data: Any, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        try:
            date_str = str(input_data) if input_data else self.get_config("date_string")
            if not date_str:
                dt = datetime.now()
            else:
                in_fmt = self.get_config("input_format", "ISO")
                if in_fmt == "ISO":
                    dt = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
                else:
                    dt = datetime.strptime(date_str, in_fmt)
            
            out_fmt = self.get_config("output_format", "%Y-%m-%d %H:%M:%S")
            return {
                "status": "success",
                "data": {
                    "result": dt.strftime(out_fmt),
                    "timestamp": dt.timestamp(),
                    "iso": dt.isoformat()
                }
            }
        except Exception as e:
            return {"status": "error", "error": f"Date error: {str(e)}"}

@register_node("math_operation")
class MathOperationNode(BaseNode):
    """
    Performs basic arithmetic operations.
    """
    node_type = "math_operation"
    version = "1.0.0"
    category = "logic"
    
    inputs = {
        "value_a": {"type": "number"},
        "value_b": {"type": "number"},
        "operation": {
            "type": "string",
            "enum": ["add", "subtract", "multiply", "divide", "modulo", "round"],
            "default": "add"
        },
        "precision": {"type": "number", "default": 2}
    }
    outputs = {
        "result": {"type": "number"},
        "status": {"type": "string"}
    }

    async def execute(self, input_data: Any, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        try:
            # Handle list input (e.g. from previous node)
            if isinstance(input_data, list) and len(input_data) >= 2:
                a = float(input_data[0])
                b = float(input_data[1])
            else:
                a = float(input_data) if input_data is not None else float(self.get_config("value_a", 0))
                b = float(self.get_config("value_b", 0))
                
            op = self.get_config("operation", "add")
            
            result = 0.0
            if op == "add":
                result = a + b
            elif op == "subtract":
                result = a - b
            elif op == "multiply":
                result = a * b
            elif op == "divide":
                if b == 0: return {"status": "error", "error": "Division by zero"}
                result = a / b
            elif op == "modulo":
                result = a % b
            elif op == "round":
                precision = int(self.get_config("precision", 2))
                result = round(a, precision)

            return {
                "status": "success",
                "data": {"result": result}
            }
        except Exception as e:
            return {"status": "error", "error": f"Math error: {str(e)}"}
