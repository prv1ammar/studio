from typing import Any, Dict, List, Optional
from ..base import BaseNode

class BaseAgentNode(BaseNode):
    """
    Shared logic for specialized LangChain Agent nodes.
    Provides helpers to gather LLM, Tools, and Memory from the context.
    """
    category = "agents"

    async def get_tools_from_context(self, context: Optional[Dict[str, Any]] = None) -> List[Any]:
        """
        Extracts LangChain Tools from the context.
        Expects a list of tool objects under the 'tools' key.
        """
        if not context:
            return []
        
        # Tools can be passed directly via 'tools' 
        tools = context.get("tools", [])
        
        # Or gathered from results of preceding nodes if the engine supports it
        # (This depends on the Workflow implementation in worker.py)
        return tools

    async def get_llm_from_context(self, context: Optional[Dict[str, Any]] = None) -> Any:
        """
        Extracts the BaseLanguageModel (LLM) object from the context.
        """
        if not context:
            return None
        
        return context.get("llm")

    async def get_memory_from_context(self, context: Optional[Dict[str, Any]] = None) -> Any:
        """
        Extracts the BaseChatMessageHistory or BaseChatMemory from the context.
        """
        if not context:
            return None
            
        return context.get("chat_history") or context.get("memory")
