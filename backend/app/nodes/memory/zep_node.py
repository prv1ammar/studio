"""
Zep Memory Node - Studio Standard (Universal Method)
Batch 115: Specialized Tools
"""
from typing import Any, Dict, Optional, List
import aiohttp
from ..base import BaseNode
from ..registry import register_node

@register_node("zep_node")
class ZepNode(BaseNode):
    """
    Long-term memory for AI agents using Zep.
    """
    node_type = "zep_node"
    version = "1.0.0"
    category = "memory"
    credentials_required = ["zep_auth"]


    properties = [
        {
            'displayName': 'Operation',
            'name': 'operation',
            'type': 'options',
            'default': 'get_messages',
            'options': [
                {'name': 'Add Message', 'value': 'add_message'},
                {'name': 'Get Messages', 'value': 'get_messages'},
                {'name': 'Search Memory', 'value': 'search_memory'},
            ],
            'description': 'Zep action to perform',
        },
        {
            'displayName': 'Role',
            'name': 'role',
            'type': 'options',
            'default': 'user',
            'options': [
                {'name': 'User', 'value': 'user'},
                {'name': 'Assistant', 'value': 'assistant'},
                {'name': 'System', 'value': 'system'},
            ],
        },
        {
            'displayName': 'Session Id',
            'name': 'session_id',
            'type': 'string',
            'default': '',
            'description': 'Session ID for the conversation',
            'required': True,
        },
        {
            'displayName': 'Text',
            'name': 'text',
            'type': 'string',
            'default': '',
            'description': 'Message text to add or search for',
        },
    ]
    inputs = {
        "action": {
            "type": "dropdown",
            "default": "get_messages",
            "options": ["add_message", "get_messages", "search_memory"],
            "description": "Zep action to perform"
        },
        "session_id": {
            "type": "string",
            "required": True,
            "description": "Session ID for the conversation"
        },
        "text": {
            "type": "string",
            "optional": True,
            "description": "Message text to add or search for"
        },
        "role": {
            "type": "dropdown",
            "default": "user",
            "options": ["user", "assistant", "system"]
        }
    }

    outputs = {
        "results": {"type": "list"},
        "status": {"type": "string"}
    }

    async def execute(self, input_data: Any, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        try:
            creds = await self.get_credential("zep_auth")
            api_url = creds.get("api_url", "http://localhost:8000").rstrip('/')
            api_key = creds.get("api_key")
            
            headers = {"Content-Type": "application/json"}
            if api_key:
                headers["Authorization"] = f"Bearer {api_key}"

            action = self.get_config("action", "get_messages")
            session_id = self.get_config("session_id")
            text = self.get_config("text") or str(input_data)
            role = self.get_config("role", "user")

            async with aiohttp.ClientSession() as session:
                if action == "get_messages":
                    async with session.get(f"{api_url}/api/v1/sessions/{session_id}/messages", headers=headers) as response:
                        data = await response.json()
                        return {"status": "success", "data": {"results": data.get("messages", [])}}

                elif action == "add_message":
                    payload = {
                        "messages": [{"role": role, "content": text}]
                    }
                    async with session.post(f"{api_url}/api/v1/sessions/{session_id}/messages", headers=headers, json=payload) as response:
                        data = await response.json()
                        return {"status": "success", "data": {"results": data}}

                elif action == "search_memory":
                    payload = {"text": text}
                    async with session.post(f"{api_url}/api/v1/sessions/{session_id}/search", headers=headers, json=payload) as response:
                        data = await response.json()
                        return {"status": "success", "data": {"results": data}}

            return {"status": "error", "error": f"Unsupported action: {action}"}

        except Exception as e:
            return {"status": "error", "error": f"Zep failure: {str(e)}"}