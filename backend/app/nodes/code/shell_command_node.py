"""
Shell Command Node - Studio Standard
Batch 43: Code Execution
"""
from typing import Any, Dict, Optional
import asyncio
from ..base import BaseNode
from ..registry import register_node

@register_node("shell_command")
class ShellCommandNode(BaseNode):
    """
    Execute shell commands.
    WARNING: Highly dangerous. Ensure user permissions are restricted.
    """
    node_type = "shell_command"
    version = "1.0.0"
    category = "code"
    credentials_required = []


    properties = [
        {
            'displayName': 'Command',
            'name': 'command',
            'type': 'string',
            'default': '',
            'description': 'Shell command to execute',
            'required': True,
        },
        {
            'displayName': 'Cwd',
            'name': 'cwd',
            'type': 'string',
            'default': '',
            'description': 'Current working directory',
        },
        {
            'displayName': 'Timeout',
            'name': 'timeout',
            'type': 'string',
            'default': 30,
            'description': 'Timeout in seconds',
        },
    ]
    inputs = {
        "command": {
            "type": "string",
            "required": True,
            "description": "Shell command to execute"
        },
        "cwd": {
            "type": "string",
            "optional": True,
            "description": "Current working directory"
        },
        "timeout": {
            "type": "number",
            "default": 30,
            "description": "Timeout in seconds"
        }
    }

    outputs = {
        "stdout": {"type": "string"},
        "stderr": {"type": "string"},
        "returncode": {"type": "number"}
    }

    async def execute(self, input_data: Any, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        command = self.get_config("command")
        
        # Override from input
        if isinstance(input_data, str) and input_data:
            command = input_data
        
        if not command:
            return {"status": "error", "error": "Command is required."}

        cwd = self.get_config("cwd") or None
        timeout = int(self.get_config("timeout", 30))

        try:
            # Create subprocess
            proc = await asyncio.create_subprocess_shell(
                command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=cwd
            )

            try:
                stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=timeout)
                
                return {
                    "status": "success",
                    "data": {
                        "stdout": stdout.decode().strip(),
                        "stderr": stderr.decode().strip(),
                        "returncode": proc.returncode
                    }
                }
            except asyncio.TimeoutError:
                proc.kill()
                return {"status": "error", "error": f"Command timed out after {timeout} seconds."}

        except Exception as e:
            return {"status": "error", "error": f"Shell Execution Failed: {str(e)}"}