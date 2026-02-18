"""
JavaScript Code Execution Node - Studio Standard
Batch 43: Code Execution
"""
from typing import Any, Dict, Optional
import json
import asyncio
import os
import tempfile
from ..base import BaseNode
from ..registry import register_node

@register_node("javascript_code")
class JavaScriptCodeNode(BaseNode):
    """
    Execute JavaScript code using Node.js.
    Input data is available as 'inputs' variable.
    Must return JSON via console.log(JSON.stringify(result)).
    """
    node_type = "javascript_code"
    version = "1.0.0"
    category = "code"
    credentials_required = []


    properties = [
        {
            'displayName': 'Code',
            'name': 'code',
            'type': 'json',
            'default': 'const result = inputs;
console.log(JSON.stringify(result));',
            'description': 'JavaScript code to execute',
        },
        {
            'displayName': 'Inputs',
            'name': 'inputs',
            'type': 'string',
            'default': '',
            'description': 'Input data available as 'inputs'',
        },
        {
            'displayName': 'Packages',
            'name': 'packages',
            'type': 'string',
            'default': '',
            'description': 'NPM packages to simulate (not supported in simple mode yet)',
        },
    ]
    inputs = {
        "code": {
            "type": "code",
            "language": "javascript",
            "default": "const result = inputs;\nconsole.log(JSON.stringify(result));",
            "description": "JavaScript code to execute"
        },
        "inputs": {
            "type": "json",
            "description": "Input data available as 'inputs'"
        },
        "packages": {
            "type": "string",
            "description": "NPM packages to simulate (not supported in simple mode yet)"
        }
    }

    outputs = {
        "result": {"type": "any"},
        "stdout": {"type": "string"},
        "error": {"type": "string"}
    }

    async def execute(self, input_data: Any, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        code = self.get_config("code", "")
        
        # Prepare Inputs
        user_inputs = input_data
        if hasattr(input_data, "dict"):
            user_inputs = input_data.dict()
        if not user_inputs:
            user_inputs = self.get_config("inputs", {})

        # Wrap user code to inject inputs
        wrapped_code = f"""
        const inputs = {json.dumps(user_inputs)};
        try {{
            {code}
        }} catch (e) {{
            console.error(e);
            process.exit(1);
        }}
        """

        # Write to temp file
        with tempfile.NamedTemporaryFile(mode="w", suffix=".js", delete=False) as f:
            f.write(wrapped_code)
            temp_js_path = f.name

        try:
            # Execute Node.js
            proc = await asyncio.create_subprocess_exec(
                "node", temp_js_path,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await proc.communicate()
            
            stdout_str = stdout.decode().strip()
            stderr_str = stderr.decode().strip()

            if proc.returncode != 0:
                return {
                    "status": "error",
                    "error": stderr_str,
                    "data": {"stdout": stdout_str}
                }

            # Try to parse last line as JSON result
            try:
                # If multiple lines, take the last one as result
                lines = stdout_str.splitlines()
                result_json = json.loads(lines[-1]) if lines else None
                return {
                    "status": "success",
                    "data": {
                        "result": result_json,
                        "stdout": stdout_str,
                        "error": None
                    }
                }
            except json.JSONDecodeError:
                 return {
                    "status": "success", 
                    "data": {
                        "result": stdout_str, # Fallback to string
                        "stdout": stdout_str,
                        "error": "Could not parse JSON output"
                    }
                }

        except FileNotFoundError:
             return {"status": "error", "error": "Node.js not found. Please install Node.js."}
        except Exception as e:
             return {"status": "error", "error": f"JS Execution Failed: {str(e)}"}
        finally:
            if os.path.exists(temp_js_path):
                os.remove(temp_js_path)