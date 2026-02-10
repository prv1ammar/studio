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
            llm = self._build_model()
            user_input = input_data if input_data else self.config.get("input", "")
            if not user_input:
                return "Error: No input provided to OpenAI Node"

            response = llm.invoke(str(user_input))
            return response.content
        except Exception as e:
            return f"OpenAI Execution Error: {str(e)}"

    def _build_model(self):
        from langchain_openai import ChatOpenAI
        api_key = self.config.get("api_key") or os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("API Key is required for OpenAI Node")
            
        return ChatOpenAI(
            api_key=api_key,
            model=self.config.get("model", "gpt-4o"),
            temperature=float(self.config.get("temperature", 0.7)),
            max_tokens=int(self.config.get("max_tokens", 1000))
        )

    async def get_langchain_object(self, context: Optional[Dict[str, Any]] = None) -> Any:
        try:
            return self._build_model()
        except:
            return None
