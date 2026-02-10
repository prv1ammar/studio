from typing import Any, Dict, Optional
from ..base import BaseNode
from ..registry import register_node
import os

@register_node("googleNode")
class GoogleNode(BaseNode):
    """
    Official Google Gemini Node implementation.
    Executes standard Google Generative AI chat completions.
    """
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.node_type = "google_gemini"

    async def execute(self, input_data: Any, context: Optional[Dict[str, Any]] = None) -> str:
        try:
            import google.generativeai as genai
            
            # Extract config
            api_key = self.config.get("api_key") or os.getenv("GOOGLE_API_KEY")
            if not api_key:
                return "Error: API Key is required for Google Node"
                
            model_name = self.config.get("model", "gemini-pro")
            temperature = float(self.config.get("temperature", 0.7))
            
            # Helper to handle input being passed directly or config
            user_input = input_data if input_data else self.config.get("input", "")
            if not user_input:
                return "Error: No input provided to Google Node"

            # Configure
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel(model_name)
            
            # Generation config
            generation_config = genai.types.GenerationConfig(
                temperature=temperature
            )
            
            print(f"[GoogleNode] Sending request to {model_name}...")
            
            # Execute
            response = await model.generate_content_async(
                str(user_input),
                generation_config=generation_config
            )
            
            result = response.text
            print(f"[GoogleNode] Received response: {result[:50]}...")
            return result
            
        except ImportError:
            return "Error: 'google-generativeai' package not installed. Please run: pip install google-generativeai"
        except Exception as e:
            print(f"[GoogleNode] Error: {e}")
            return f"Google Execution Error: {str(e)}"
