"""
Redis Chat Memory Node - Studio Standard
Batch 39: Memory & History
"""
from typing import Any, Dict, Optional, List
from ..base import BaseNode
from ..registry import register_node

@register_node("redis_chat_memory")
class RedisChatMemoryNode(BaseNode):
    """
    Persistent chat memory backed by Redis.
    Allows for long-term conversation storage.
    """
    node_type = "redis_chat_memory"
    version = "1.0.0"
    category = "memory"
    credentials_required = ["redis_auth"]


    properties = [
        {
            'displayName': 'Input Key',
            'name': 'input_key',
            'type': 'string',
            'default': 'input',
            'description': 'Key for user input',
        },
        {
            'displayName': 'K',
            'name': 'k',
            'type': 'string',
            'default': 10,
            'description': 'Number of recent messages to keep in active buffer',
        },
        {
            'displayName': 'Output Key',
            'name': 'output_key',
            'type': 'string',
            'default': 'output',
            'description': 'Key for AI output',
        },
        {
            'displayName': 'Redis Url',
            'name': 'redis_url',
            'type': 'string',
            'default': 'redis://localhost:6379',
            'description': 'Redis connection URL',
        },
        {
            'displayName': 'Return Messages',
            'name': 'return_messages',
            'type': 'boolean',
            'default': True,
            'description': 'Return messages list or string history',
        },
        {
            'displayName': 'Session Id',
            'name': 'session_id',
            'type': 'string',
            'default': '',
            'description': 'Unique session identifier',
            'required': True,
        },
        {
            'displayName': 'Ttl',
            'name': 'ttl',
            'type': 'string',
            'default': '',
            'description': 'Time-to-live in seconds (optional)',
        },
    ]
    inputs = {
        "redis_url": {
            "type": "string",
            "default": "redis://localhost:6379",
            "description": "Redis connection URL"
        },
        "session_id": {
            "type": "string",
            "required": True,
            "description": "Unique session identifier"
        },
        "k": {
            "type": "number",
            "default": 10,
            "description": "Number of recent messages to keep in active buffer"
        },
        "ttl": {
            "type": "number",
            "optional": True,
            "description": "Time-to-live in seconds (optional)"
        },
        "input_key": {
            "type": "string",
            "default": "input",
            "description": "Key for user input"
        },
        "output_key": {
            "type": "string",
            "default": "output",
            "description": "Key for AI output"
        },
        "return_messages": {
            "type": "boolean",
            "default": True,
            "description": "Return messages list or string history"
        }
    }

    outputs = {
        "memory": {"type": "object"},
        "history": {"type": "string"},
        "messages": {"type": "array"}
    }

    async def execute(self, input_data: Any, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        try:
            from langchain.memory import ConversationBufferWindowMemory
            from langchain_community.chat_message_histories import RedisChatMessageHistory
            from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage

            # Get configuration
            redis_url = self.get_config("redis_url", "redis://localhost:6379")
            session_id = input_data if isinstance(input_data, str) else self.get_config("session_id")
            
            if not session_id:
                return {"status": "error", "error": "session_id is required"}

            k = int(self.get_config("k", 10))
            ttl = self.get_config("ttl")
            if ttl is not None:
                ttl = int(ttl)

            input_key = self.get_config("input_key")
            output_key = self.get_config("output_key")
            return_messages = self.get_config("return_messages", True)

            # Create Backend History
            try:
                message_history = RedisChatMessageHistory(
                    url=redis_url,
                    session_id=session_id,
                    ttl=ttl
                )
            except Exception as e:
                return {"status": "error", "error": f"Failed to connect to Redis: {str(e)}"}

            # Create Memory Object
            memory = ConversationBufferWindowMemory(
                chat_memory=message_history,
                k=k,
                input_key=input_key,
                output_key=output_key,
                return_messages=return_messages,
                memory_key="chat_history"
            )

            # Retrieve current history for display
            messages = message_history.messages  # Direct access to history
            history_str = "\n".join([f"{type(m).__name__}: {m.content}" for m in messages])
            
            # Format messages for output
            formatted_messages = []
            for m in messages:
                role = "user" if isinstance(m, HumanMessage) else "assistant" if isinstance(m, AIMessage) else "system"
                formatted_messages.append({"role": role, "content": m.content})

            return {
                "status": "success",
                "data": {
                    "memory": memory,
                    "history": history_str,
                    "messages": formatted_messages,
                    "count": len(messages)
                }
            }

        except ImportError:
            return {
                "status": "error",
                "error": "Required libraries missing. Run: pip install langchain-community redis"
            }
        except Exception as e:
            return {
                "status": "error",
                "error": f"Redis Memory failed: {str(e)}"
            }

    async def get_langchain_object(self, context: Optional[Dict[str, Any]] = None) -> Any:
        result = await self.execute(None, context)
        if result["status"] == "success":
            return result["data"]["memory"]
        raise ValueError(result.get("error", "Unknown error"))