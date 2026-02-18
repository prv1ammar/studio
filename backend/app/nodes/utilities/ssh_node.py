"""
SSH Node - Studio Standard (Universal Method)
Batch 111: Utilities & Data Processing
"""
from typing import Any, Dict, Optional
import aiohttp
from ..base import BaseNode
from ..registry import register_node

# Requires `asyncssh` for async SSH
# We'll implement structure for asyncssh.

@register_node("ssh_node")
class SSHNode(BaseNode):
    """
    Execute commands on a remote server via SSH.
    """
    node_type = "ssh_node"
    version = "1.0.0"
    category = "utilities"
    credentials_required = ["ssh_auth"]


    properties = [
        {
            'displayName': 'Operation',
            'name': 'operation',
            'type': 'options',
            'default': 'execute_command',
            'options': [
                {'name': 'Execute Command', 'value': 'execute_command'},
                {'name': 'Upload File', 'value': 'upload_file'},
                {'name': 'Download File', 'value': 'download_file'},
            ],
            'description': 'SSH action',
        },
        {
            'displayName': 'Command',
            'name': 'command',
            'type': 'string',
            'default': '',
        },
    ]
    inputs = {
        "action": {
            "type": "dropdown",
            "default": "execute_command",
            "options": ["execute_command", "upload_file", "download_file"],
            "description": "SSH action"
        },
        "command": {
            "type": "string",
            "optional": True
        }
    }

    outputs = {
        "result": {"type": "any"},
        "status": {"type": "string"}
    }

    async def execute(self, input_data: Any, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        try:
            import asyncssh
        except ImportError:
            return {"status": "error", "error": "asyncssh library not installed. Please install it to use SSH Node."}

        try:
            creds = await self.get_credential("ssh_auth")
            host = creds.get("host")
            port = int(creds.get("port", 22))
            username = creds.get("username")
            password = creds.get("password")
            private_key = creds.get("private_key")
            
            if not host or not username:
                return {"status": "error", "error": "SSH Host and Username required"}

            action = self.get_config("action", "execute_command")
            
            client_keys = None
            if private_key:
                # Need to load key properly, simplified here
                # client_keys = [asyncssh.import_private_key(private_key)]
                pass # Complex key handling
            
            async with asyncssh.connect(host, port=port, username=username, password=password, client_keys=client_keys, known_hosts=None) as conn:
                if action == "execute_command":
                    command = self.get_config("command")
                    if not command: return {"status": "error", "error": "command required"}
                    
                    result = await conn.run(command, check=True)
                    return {"status": "success", "data": {"result": {"stdout": result.stdout, "stderr": result.stderr, "exit_status": result.exit_status}}}

            return {"status": "error", "error": f"Unsupported action: {action}"}

        except Exception as e:
            return {"status": "error", "error": f"SSH Node Failed: {str(e)}"}