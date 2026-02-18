"""
Mem0 Node - Studio Standard (Universal Method)
Batch 114: Advanced AI Frameworks & Memory
"""
from typing import Any, Dict, Optional, List
from ..base import BaseNode
from ..registry import register_node

@register_node("mem0_node")
class Mem0Node(BaseNode):
    """
    Long-term memory for AI agents using Mem0.
    """
    node_type = "mem0_node"
    version = "1.0.0"
    category = "memory"
    credentials_required = ["mem0_auth"]


    properties = [
        {
            'displayName': 'Operation',
            'name': 'operation',
            'type': 'options',
            'default': 'add',
            'options': [
                {'name': 'Add', 'value': 'add'},
                {'name': 'Search', 'value': 'search'},
                {'name': 'Get All', 'value': 'get_all'},
                {'name': 'Delete All', 'value': 'delete_all'},
            ],
            'description': 'Action to perform',
        },
        {
            'displayName': 'Query',
            'name': 'query',
            'type': 'string',
            'default': '',
            'description': 'The message to store or search for',
        },
        {
            'displayName': 'User Id',
            'name': 'user_id',
            'type': 'string',
            'default': '',
            'description': 'Unique identifier for the user',
            'required': True,
        },
    ]
    inputs = {
        "action": {
            "type": "dropdown",
            "default": "add",
            "options": ["add", "search", "get_all", "delete_all"],
            "description": "Action to perform"
        },
        "query": {
            "type": "string",
            "optional": True,
            "description": "The message to store or search for"
        },
        "user_id": {
            "type": "string",
            "required": True,
            "description": "Unique identifier for the user"
        }
    }

    outputs = {
        "results": {"type": "list"},
        "status": {"type": "string"}
    }

    async def execute(self, input_data: Any, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        try:
            from mem0 import Memory
        except ImportError:
            return {"status": "error", "error": "mem0ai not installed"}

        try:
            creds = await self.get_credential("mem0_auth")
            api_key = creds.get("api_key")
            
            # Simple initialization - Mem0 handles cloud if api_key provided
            m = Memory() if not api_key else Memory(api_key=api_key)
            
            action = self.get_config("action", "add")
            user_id = self.get_config("user_id")
            query = self.get_config("query") or str(input_data)

            if action == "add":
                res = m.add(query, user_id=user_id)
                return {"status": "success", "data": {"results": res}}
            elif action == "search":
                res = m.search(query, user_id=user_id)
                return {"status": "success", "data": {"results": res}}
            elif action == "get_all":
                res = m.get_all(user_id=user_id)
                return {"status": "success", "data": {"results": res}}

            return {"status": "error", "error": f"Invalid action: {action}"}

        except Exception as e:
            return {"status": "error", "error": f"Mem0 operation failed: {str(e)}"}