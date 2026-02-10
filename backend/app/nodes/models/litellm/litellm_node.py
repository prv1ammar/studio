from ...base import BaseNode
from ...registry import register_node
from typing import Any, Dict, Optional
from langchain_openai import ChatOpenAI

@register_node("liteLLM")
class LiteLLMNode(BaseNode):
    def _build_model(self):
        api_key = self.config.get("api_key", "sk-RVApjtnPznKZ4UXosZYEOQ").strip()
        base_url = self.config.get("base_url", "https://toknroutertybot.tybotflow.com/").strip()
        model = self.config.get("model_name", "gpt-4.1-mini")
        temperature = float(self.config.get("temperature", 0.1))
        
        return ChatOpenAI(api_key=api_key, base_url=base_url, model=model, temperature=temperature)

    async def execute(self, input_data: str, context: Optional[Dict[str, Any]] = None) -> str:
        try:
            llm = self._build_model()
            response = llm.invoke(input_data)
            return response.content
        except Exception as e:
            return f"LiteLLM Error: {str(e)}"

    async def get_langchain_object(self, context: Optional[Dict[str, Any]] = None) -> Any:
        return self._build_model()
