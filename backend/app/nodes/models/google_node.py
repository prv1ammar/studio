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
    node_type = "google_gemini"
    version = "1.0.0"
    category = "ai"
    inputs = {
        "model": {"type": "string", "default": "gemini-pro"},
        "temperature": {"type": "number", "default": 0.7},
        "input": {"type": "string", "description": "User prompt"}
    }
    outputs = {
        "text": {"type": "string", "description": "Generated response"},
        "status": {"type": "string"}
    }
    credentials_required = ["google_api_key"]

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)

    async def execute(self, input_data: Any, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        try:
            import google.generativeai as genai
            
            # 1. Try Secrets Manager
            creds = await self.get_credential("credentials_id")
            api_key = creds.get("api_key") if creds else None
            
            # 2. Fallback to config or ENV
            if not api_key:
                api_key = self.get_config("api_key") or os.getenv("GOOGLE_API_KEY")
                
            if not api_key:
                return {"status": "error", "error": "API Key is required for Google Node"}
                
            model_name = self.get_config("model", "gemini-pro")
            temperature = float(self.get_config("temperature", 0.7))
            
            # Helper to handle input being passed directly or config
            user_input = input_data if input_data else self.get_config("input", "")
            if not user_input:
                return {"status": "error", "error": "No input provided to Google Node"}

            # Configure
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel(model_name)
            
            # Generation config
            generation_config = genai.types.GenerationConfig(
                temperature=temperature
            )
            
            # Execute
            response = await model.generate_content_async(
                str(user_input),
                generation_config=generation_config
            )
            
            result = response.text
            return {"status": "success", "data": {"text": result}}
            
        except ImportError:
            return {"status": "error", "error": "Error: 'google-generativeai' package not installed. Please run: pip install google-generativeai"}
        except Exception as e:
            return {"status": "error", "error": f"Google Execution Error: {str(e)}"}
