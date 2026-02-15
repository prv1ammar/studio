from typing import Any, Dict, Optional
from app.nodes.base import BaseNode
from app.nodes.factory import register_node
from pydantic import BaseModel, Field

class TranslationConfig(BaseModel):
    source_lang: str = Field(default="auto", description="Source language (e.g., 'English')")
    target_lang: str = Field(..., description="Target language (e.g., 'French')")
    provider: str = Field(default="openai", description="AI Provider to use for translation")

class TranslationInput(BaseModel):
    text: str = Field(..., description="The text to translate")

@register_node("translation_node")
class TranslationNode(BaseNode):
    """
    Globalization Engine: Translation Node.
    Uses AI to translate text between languages while preserving context.
    """
    name = "Translate Text"
    description = "Translate text between languages using AI."
    category = "Globalization"
    node_type = "translation_node"
    
    config_model = TranslationConfig
    input_model = TranslationInput

    async def execute(self, input_data: TranslationInput, context: Optional[Dict[str, Any]] = None) -> Any:
        # We leverage the internal engine's AI capabilities
        from app.core.engine import engine
        
        target = self.get_config("target_lang")
        source = self.get_config("source_lang")
        
        prompt = f"Translate the following text from {source} to {target}. ONLY return the translated text without quotes or explanations:\n\n{input_data.text}"
        
        # We route through LiteLLM for high-quality translation
        result = await engine.execute_node(
            "liteLLM", 
            prompt, 
            config={"model": "gpt-4o-mini", "provider": self.get_config("provider")}, 
            context={"user_id": context.get("user_id") if context else None}
        )
        
        translated_text = result if isinstance(result, str) else result.get("data", str(result))
        
        return {
            "translated_text": translated_text,
            "source_lang": source,
            "target_lang": target
        }
