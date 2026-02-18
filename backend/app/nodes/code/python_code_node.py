"""
Python Code Execution Node - Studio Standard
Batch 43: Code Execution
"""
from typing import Any, Dict, Optional, List
import sys
import io
import contextlib
import traceback
from ..base import BaseNode
from ..registry import register_node

@register_node("python_code")
class PythonCodeNode(BaseNode):
    """
    Execute custom Python code.
    Can return structured data by defining a 'main' function or assigning to 'output'.
    """
    node_type = "python_code"
    version = "1.0.0"
    category = "code"
    credentials_required = []


    properties = [
        {
            'displayName': 'Code',
            'name': 'code',
            'type': 'json',
            'default': 'def main(inputs):
    return inputs',
            'description': 'Python code to execute',
        },
        {
            'displayName': 'Imports',
            'name': 'imports',
            'type': 'string',
            'default': '',
            'description': 'Comma-separated list of modules to import (e.g., 'math, json')',
        },
        {
            'displayName': 'Inputs',
            'name': 'inputs',
            'type': 'string',
            'default': '',
            'description': 'Input data available as 'inputs' variable',
        },
    ]
    inputs = {
        "code": {
            "type": "code",
            "language": "python",
            "default": "def main(inputs):\n    return inputs",
            "description": "Python code to execute"
        },
        "inputs": {
            "type": "json",
            "description": "Input data available as 'inputs' variable"
        },
        "imports": {
            "type": "string",
            "description": "Comma-separated list of modules to import (e.g., 'math, json')"
        }
    }

    outputs = {
        "result": {"type": "any"},
        "stdout": {"type": "string"},
        "error": {"type": "string"}
    }

    async def execute(self, input_data: Any, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        code = self.get_config("code", "")
        # Handle input data
        user_inputs = input_data
        if hasattr(input_data, "dict"):
            user_inputs = input_data.dict()
        
        # Override from config if input_data is not primary
        if not user_inputs:
             user_inputs = self.get_config("inputs", {})

        imports_str = self.get_config("imports", "")
        
        # Prepare environment
        local_scope = {"inputs": user_inputs, "output": None}
        global_scope = {"__builtins__": __builtins__}

        # Handle imports
        if imports_str:
            for mod_name in imports_str.split(","):
                mod_name = mod_name.strip()
                if mod_name:
                    try:
                        mod = __import__(mod_name)
                        global_scope[mod_name] = mod
                    except ImportError as e:
                        return {"status": "error", "error": f"Failed to import '{mod_name}': {str(e)}"}

        stdout_capture = io.StringIO()
        result = None
        error = None

        try:
            with contextlib.redirect_stdout(stdout_capture):
                # Execute the code
                exec(code, global_scope, local_scope)
                
                # Check for 'main' function
                if "main" in local_scope and callable(local_scope["main"]):
                    result = local_scope["main"](user_inputs)
                # Check for 'output' variable
                elif local_scope.get("output") is not None:
                    result = local_scope["output"]
                else:
                    # Provide stdout as result if no structured return
                    result = stdout_capture.getvalue()

        except Exception:
            error = traceback.format_exc()
            return {
                "status": "error",
                "error": error,
                "data": {
                    "stdout": stdout_capture.getvalue()
                }
            }

        return {
            "status": "success",
            "data": {
                "result": result,
                "stdout": stdout_capture.getvalue(),
                "error": None
            }
        }