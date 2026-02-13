"""
Mistral Model Node - Studio Standard
Batch 36: AI Chat Models
"""
from typing import Any, Dict, Optional, List
from ...base import BaseNode
from ...registry import register_node

@register_node("mistral_model")
class MistralModelNode(BaseNode):
    """
    Generate text using Mistral AI models.
    Supports Mistral Large, Small, and 8x7B (Mixtral).
    """
    node_type = "mistral_model"
    version = "1.0.0"
    category = "ai_models"
    credentials_required = ["mistral_auth"]

    inputs = {
        "model_name": {
            "type": "dropdown",
            "default": "mistral-large-latest",
            "options": [
                "mistral-large-latest",
                "open-mixtral-8x7b",
                "open-mistral-7b",
                "mistral-small-latest",
                "mistral-medium-latest"
            ],
            "description": "Mistral model to use"
        },
        "mistral_api_key": {
            "type": "string",
            "optional": True,
            "description": "Mistral API key (overrides credential)"
        },
        "max_tokens": {
            "type": "number",
            "default": 1024,
            "description": "Maximum number of tokens to generate"
        },
        "temperature": {
            "type": "number",
            "default": 0.7,
            "description": "Controls randomness (0.0 to 1.0)"
        },
        "system_message": {
            "type": "string",
            "optional": True,
            "description": "System message for the model"
        },
        "stream": {
            "type": "boolean",
            "default": False,
            "description": "Stream the response"
        }
    }

    outputs = {
        "text": {"type": "string"},
        "model": {"type": "object"},
        "response_metadata": {"type": "object"}
    }

    async def execute(self, input_data: Any, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        try:
            # Import dependencies
            try:
                from langchain_mistralai import ChatMistralAI
                from langchain_core.messages import HumanMessage, SystemMessage
            except ImportError:
                return {
                    "status": "error",
                    "error": "langchain-mistralai not installed. Run: pip install langchain-mistralai"
                }

            # Get credentials
            creds = await self.get_credential("mistral_auth")
            api_key = creds.get("api_key") if creds else self.get_config("mistral_api_key")
            
            if not api_key:
                return {"status": "error", "error": "Mistral API Key is required"}

            # Get configuration
            model_name = self.get_config("model_name", "mistral-large-latest")
            max_tokens = int(self.get_config("max_tokens", 1024))
            temperature = float(self.get_config("temperature", 0.7))
            system_msg = self.get_config("system_message")
            stream = self.get_config("stream", False)

            # Initialize model
            llm = ChatMistralAI(
                model=model_name,
                mistral_api_key=api_key,
                max_tokens=max_tokens,
                temperature=temperature,
                streaming=stream
            )

            # If input provided, generate response
            input_text = input_data if isinstance(input_data, str) else self.get_config("input_value")
            
            if input_text:
                messages = []
                if system_msg:
                    messages.append(SystemMessage(content=system_msg))
                
                messages.append(HumanMessage(content=input_text))
                
                response = await llm.ainvoke(messages)
                
                return {
                    "status": "success",
                    "data": {
                        "text": response.content,
                        "model": llm,
                        "response_metadata": response.response_metadata
                    }
                }
            
            # If no input, just return the model object
            return {
                "status": "success",
                "data": {
                    "model": llm,
                    "text": ""
                }
            }

        except Exception as e:
            return {
                "status": "error",
                "error": f"Mistral Model failed: {str(e)}"
            }

    async def get_langchain_object(self, context: Optional[Dict[str, Any]] = None) -> Any:
        result = await self.execute(None, context)
        if result["status"] == "success":
            return result["data"]["model"]
        raise ValueError(result.get("error", "Unknown error"))
