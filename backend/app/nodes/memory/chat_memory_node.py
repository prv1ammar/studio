"""
Chat Memory Node - Studio Standard
Batch 39: Memory & History
"""
from typing import Any, Dict, Optional
from ..base import BaseNode
from ..registry import register_node

@register_node("chat_memory")
class ChatMemoryNode(BaseNode):
    """
    Manages chat history for AI agents.
    Provides a sliding window of recent messages to keep context within limits.
    """
    node_type = "chat_memory"
    version = "1.0.0"
    category = "memory"
    credentials_required = []


    properties = [
        {
            'displayName': 'Input Key',
            'name': 'input_key',
            'type': 'string',
            'default': 'input',
            'description': 'Key for input variable',
        },
        {
            'displayName': 'Output Key',
            'name': 'output_key',
            'type': 'string',
            'default': 'output',
            'description': 'Key for output variable',
        },
        {
            'displayName': 'Return Messages',
            'name': 'return_messages',
            'type': 'boolean',
            'default': True,
            'description': 'Return as list of messages (True) or string (False)',
        },
        {
            'displayName': 'Session Id',
            'name': 'session_id',
            'type': 'string',
            'default': '',
            'description': 'Unique session identifier',
        },
        {
            'displayName': 'Window Size',
            'name': 'window_size',
            'type': 'string',
            'default': 10,
            'description': 'Number of messages to keep in history',
        },
    ]
    inputs = {
        "window_size": {
            "type": "number",
            "default": 10,
            "description": "Number of messages to keep in history"
        },
        "session_id": {
            "type": "string",
            "optional": True,
            "description": "Unique session identifier"
        },
        "input_key": {
            "type": "string",
            "default": "input",
            "description": "Key for input variable"
        },
        "output_key": {
            "type": "string",
            "default": "output",
            "description": "Key for output variable"
        },
        "return_messages": {
            "type": "boolean",
            "default": True,
            "description": "Return as list of messages (True) or string (False)"
        }
    }

    outputs = {
        "memory": {"type": "object"},
        "history": {"type": "string"}
    }

    async def execute(self, input_data: Any, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        try:
            # Import dependencies
            try:
                from langchain.memory import ConversationBufferWindowMemory
            except ImportError:
                return {
                    "status": "error",
                    "error": "langchain not installed. Run: pip install langchain"
                }

            # Get configuration
            window_size = int(self.get_config("window_size", 10))
            input_key = self.get_config("input_key", "input")
            output_key = self.get_config("output_key", "output")
            return_messages = self.get_config("return_messages", True)
            
            # Create memory object
            memory = ConversationBufferWindowMemory(
                k=window_size,
                input_key=input_key,
                output_key=output_key,
                return_messages=return_messages,
                memory_key="chat_history"
            )

            # Retrieve current history (empty initially for new obj, 
            # but in a real flow, this obj is passed to an Agent which updates it)
            # To actually SHOW history, we'd need a persistent backend (like Redis).
            # This node primarily provides the *Mechanism* for an Agent.
            
            # However, for debugging, we can show what it is.
            
            return {
                "status": "success",
                "data": {
                    "memory": memory,
                    "history": "Memory initialized (Empty)"
                }
            }

        except Exception as e:
            return {
                "status": "error",
                "error": f"Chat Memory creation failed: {str(e)}"
            }

    async def get_langchain_object(self, context: Optional[Dict[str, Any]] = None) -> Any:
        result = await self.execute(None, context)
        if result["status"] == "success":
            return result["data"]["memory"]
        raise ValueError(result.get("error", "Unknown error"))