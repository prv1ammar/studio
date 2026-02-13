"""
File Chat Memory Node - Studio Standard
Batch 39: Memory & History
"""
from typing import Any, Dict, Optional, List
import json
import os
from ...base import BaseNode
from ...registry import register_node

@register_node("file_chat_memory")
class FileChatMemoryNode(BaseNode):
    """
    Persistent chat memory backed by a local JSON file.
    Ideal for local development without Redis.
    """
    node_type = "file_chat_memory"
    version = "1.0.0"
    category = "memory"
    credentials_required = []

    inputs = {
        "file_path": {
            "type": "string",
            "required": True,
            "description": "Path to the JSON file for storing history"
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
        }
    }

    outputs = {
        "memory": {"type": "object"},
        "history": {"type": "string"},
        "messages": {"type": "array"}
    }

    async def execute(self, input_data: Any, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        try:
            from langchain.memory import ConversationBufferWindowMemory, FileChatMessageHistory
            from langchain_core.messages import HumanMessage, AIMessage, SystemMessage

            # Get configuration
            file_path = self.get_config("file_path", "chat_history.json")
            session_id = input_data if isinstance(input_data, str) else self.get_config("session_id")
            k = int(self.get_config("k", 10))
            
            if not session_id:
                 return {"status": "error", "error": "session_id is required"}

            # Standardize file path
            if not os.path.isabs(file_path):
                 file_path = os.path.abspath(file_path)

            # Ensure directory exists
            os.makedirs(os.path.dirname(file_path), exist_ok=True)

            # Create File History
            # Note: FileChatMessageHistory in LangChain usually takes just a path.
            # To support sessions in one file, we'd need custom logic.
            # Standard FileChatMessageHistory writes everything to one file.
            # So let's append session_id to filename to keep them separate.
            
            base, ext = os.path.splitext(file_path)
            session_file_path = f"{base}_{session_id}{ext}"
            
            message_history = FileChatMessageHistory(file_path=session_file_path)

            # Create Memory Object
            memory = ConversationBufferWindowMemory(
                chat_memory=message_history,
                k=k,
                memory_key="chat_history",
                return_messages=True
            )

            # Retrieve current history for display
            messages = message_history.messages
            history_str = "\n".join([f"{type(m).__name__}: {m.content}" for m in messages])
            
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
                    "file_path": session_file_path,
                    "count": len(messages)
                }
            }

        except ImportError:
            return {
                "status": "error",
                "error": "langchain-community not installed."
            }
        except Exception as e:
            return {
                "status": "error",
                "error": f"File Memory failed: {str(e)}"
            }
