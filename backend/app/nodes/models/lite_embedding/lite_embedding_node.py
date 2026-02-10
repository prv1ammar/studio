from ...base import BaseNode
from typing import Any, Dict, Optional
from openai import OpenAI

class LiteEmbeddingNode(BaseNode):
    def _build_embeddings(self):
        from langchain_openai import OpenAIEmbeddings
        api_key = self.config.get("api_key", "sk-RVApjtnPznKZ4UXosZYEOQ").strip()
        base_url = self.config.get("base_url", "https://toknroutertybot.tybotflow.com/").strip()
        model = self.config.get("model_name", "text-embedding-3-small")
        
        return OpenAIEmbeddings(api_key=api_key, base_url=base_url, model=model)

    async def execute(self, input_data: Any, context: Optional[Dict[str, Any]] = None) -> Any:
        try:
            embeddings = self._build_embeddings()
            text = input_data.get("content") if isinstance(input_data, dict) else input_data
            
            vector = embeddings.embed_query(str(text))
            
            result = {
                "content": text,
                "embedding": vector,
                "metadata": input_data.get("metadata", {}) if isinstance(input_data, dict) else {"source": "manual"}
            }
            if isinstance(input_data, dict) and "table_name" in input_data:
                result["table_name"] = input_data["table_name"]
            
            return result
        except Exception as e:
            return f"Embedding Error: {str(e)}"

    async def get_langchain_object(self, context: Optional[Dict[str, Any]] = None) -> Any:
        return self._build_embeddings()
