from typing import Any, Dict, Optional, List
from ..base import BaseNode
from ..registry import register_node
import os

@register_node("openaiNode")
class OpenAINode(BaseNode):
    """
    Official OpenAI Chat Node implementation.
    Executes standard OpenAI chat completions.
    """
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.node_type = "openai_chat"

    async def execute(self, input_data: Any, context: Optional[Dict[str, Any]] = None) -> str:
        try:
            llm = await self._build_model()
            user_input = input_data if input_data else self.config.get("input", "")
            if not user_input:
                return "Error: No input provided to OpenAI Node"

            response = llm.invoke(str(user_input))
            return response.content
        except Exception as e:
            return f"OpenAI Execution Error: {str(e)}"

    async def _build_model(self):
        from langchain_openai import ChatOpenAI
        
        # 1. Try Secrets Manager
        creds = await self.get_credential("credentials_id")
        api_key = creds.get("api_key") if creds else None
        
        # 2. Fallback to config or ENV
        if not api_key:
            api_key = self.get_config("api_key") or os.getenv("OPENAI_API_KEY")
            
        if not api_key:
            raise ValueError("API Key is required for OpenAI Node")
            
        return ChatOpenAI(
            api_key=api_key,
            model=self.get_config("model", "gpt-4o"),
            temperature=float(self.get_config("temperature", 0.7)),
            max_tokens=int(self.get_config("max_tokens", 1000))
        )

    async def get_langchain_object(self, context: Optional[Dict[str, Any]] = None) -> Any:
        try:
            return await self._build_model()
        except:
            return None
