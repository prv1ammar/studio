from ...base import BaseNode
from ...registry import register_node
from typing import Any, Dict, Optional
from langchain_openai import ChatOpenAI

@register_node("liteLLM")
class LiteLLMNode(BaseNode):
    async def _build_model(self):
        # 1. Try Secrets Manager
        creds = await self.get_credential("credentials_id")
        api_key = creds.get("api_key") if creds else None
        base_url = creds.get("base_url") if creds else None
        
        # 2. Fallback to config
        if not api_key:
            api_key = self.get_config("api_key")
        if not base_url:
            base_url = self.get_config("base_url")
            
        model = self.get_config("model_name", "gpt-4.1-mini")
        temperature = float(self.get_config("temperature", 0.1))
        
        if not api_key:
            raise ValueError("API Key is required for LiteLLM Node")
        
        return ChatOpenAI(api_key=api_key, base_url=base_url, model=model, temperature=temperature)

    async def execute(self, input_data: str, context: Optional[Dict[str, Any]] = None) -> str:
        try:
            llm = await self._build_model()
            response = llm.invoke(input_data)
            return response.content
        except Exception as e:
            return f"LiteLLM Error: {str(e)}"

    async def get_langchain_object(self, context: Optional[Dict[str, Any]] = None) -> Any:
        return await self._build_model()
