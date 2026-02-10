from ..base import BaseNode
from ..registry import register_node
from typing import Any, Dict, Optional

@register_node("memoryNode")
class MemoryNode(BaseNode):
    """
    LangChain Memory Node with configurable storage backends.
    Supports: In-Memory, Redis, Windowed Memory, and more.
    """
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.memory = self._build_memory()

    def _build_memory(self):
        """Build the appropriate memory backend based on configuration."""
        backend = self.config.get("backend", "in_memory")
        
        if backend == "redis":
            return self._build_redis_memory()
        elif backend == "windowed":
            return self._build_windowed_memory()
        else:  # "in_memory" or default
            return self._build_buffer_memory()

    def _build_buffer_memory(self):
        """Standard in-memory conversation buffer."""
        from langchain_classic.memory import ConversationBufferMemory
        return ConversationBufferMemory(
            memory_key="chat_history",
            return_messages=True
        )

    def _build_windowed_memory(self):
        """Windowed memory that keeps only the last N messages."""
        from langchain_classic.memory import ConversationBufferWindowMemory
        k = int(self.config.get("window_size", 10))
        return ConversationBufferWindowMemory(
            memory_key="chat_history",
            return_messages=True,
            k=k
        )

    def _build_redis_memory(self):
        """Redis-backed persistent memory."""
        from langchain_classic.memory import ConversationBufferMemory
        from langchain_community.chat_message_histories import RedisChatMessageHistory
        
        redis_url = self.config.get("redis_url", "redis://localhost:6379/0")
        session_id = self.config.get("session_id", "default_session")
        ttl = self.config.get("ttl")  # Optional: time-to-live in seconds
        
        message_history = RedisChatMessageHistory(
            url=redis_url,
            session_id=session_id,
            ttl=ttl
        )
        
        return ConversationBufferMemory(
            memory_key="chat_history",
            return_messages=True,
            chat_memory=message_history,
            output_key="output"
        )

    async def execute(self, input_data: Any, context: Optional[Dict[str, Any]] = None) -> str:
        """Returns the current history as a string."""
        try:
            history = self.memory.load_memory_variables({}).get("chat_history", [])
            if not history:
                return "No conversation history yet."
            
            # Format for display
            formatted = []
            for msg in history:
                role = msg.__class__.__name__.replace("Message", "")
                formatted.append(f"{role}: {msg.content}")
            return "\n".join(formatted)
        except Exception as e:
            return f"Memory Error: {str(e)}"

    async def get_langchain_object(self, context: Optional[Dict[str, Any]] = None) -> Any:
        """Provide the memory object for Agent nodes."""
        return self.memory
