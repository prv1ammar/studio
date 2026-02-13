"""
Groq Model Node - Studio Standard
Batch 36: AI Chat Models
"""
from typing import Any, Dict, Optional, List
from ...base import BaseNode
from ...registry import register_node

@register_node("groq_model")
class GroqModelNode(BaseNode):
    """
    Generate text using Groq's high-speed LPU inference engine.
    Supports Llama 3, Mixtral, and Gemma models.
    """
    node_type = "groq_model"
    version = "1.0.0"
    category = "ai_models"
    credentials_required = ["groq_auth"]

    inputs = {
        "model_name": {
            "type": "dropdown",
            "default": "llama3-70b-8192",
            "options": [
                "llama3-70b-8192",
                "llama3-8b-8192",
                "mixtral-8x7b-32768",
                "gemma-7b-it"
            ],
            "description": "Groq model to use"
        },
        "groq_api_key": {
            "type": "string",
            "optional": True,
            "description": "Groq API key (overrides credential)"
        },
        "max_tokens": {
            "type": "number",
            "default": 8192,
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
                from langchain_groq import ChatGroq
                from langchain_core.messages import HumanMessage, SystemMessage
            except ImportError:
                return {
                    "status": "error",
                    "error": "langchain-groq not installed. Run: pip install langchain-groq"
                }

            # Get credentials
            creds = await self.get_credential("groq_auth")
            api_key = creds.get("api_key") if creds else self.get_config("groq_api_key")
            
            if not api_key:
                return {"status": "error", "error": "Groq API Key is required"}

            # Get configuration
            model_name = self.get_config("model_name", "llama3-70b-8192")
            max_tokens = int(self.get_config("max_tokens", 8192))
            temperature = float(self.get_config("temperature", 0.7))
            system_msg = self.get_config("system_message")
            stream = self.get_config("stream", False)

            # Initialize model
            llm = ChatGroq(
                model=model_name,
                groq_api_key=api_key,
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
                "error": f"Groq Model failed: {str(e)}"
            }

    async def get_langchain_object(self, context: Optional[Dict[str, Any]] = None) -> Any:
        result = await self.execute(None, context)
        if result["status"] == "success":
            return result["data"]["model"]
        raise ValueError(result.get("error", "Unknown error"))
