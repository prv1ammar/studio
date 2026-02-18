"""
Anthropic Model Node - Studio Standard
Batch 36: AI Chat Models
"""
from typing import Any, Dict, Optional, List
from ..base import BaseNode
from ..registry import register_node

@register_node("anthropic_model")
class AnthropicModelNode(BaseNode):
    """
    Generate text using Anthropic's Claude models.
    Supports Claude 3.5 Sonnet, Haiku, and Opus.
    """
    node_type = "anthropic_model"
    version = "1.0.0"
    category = "ai_models"
    credentials_required = ["anthropic_auth"]


    properties = [
        {
            'displayName': 'Anthropic Api Key',
            'name': 'anthropic_api_key',
            'type': 'string',
            'default': '',
            'description': 'Anthropic API key (overrides credential)',
        },
        {
            'displayName': 'Input Value',
            'name': 'input_value',
            'type': 'string',
            'default': '',
            'description': 'User message or input text',
        },
        {
            'displayName': 'Max Tokens',
            'name': 'max_tokens',
            'type': 'string',
            'default': 4096,
            'description': 'Maximum number of tokens to generate',
        },
        {
            'displayName': 'Model Name',
            'name': 'model_name',
            'type': 'options',
            'default': 'claude-3-5-sonnet-20240620',
            'options': [
                {'name': 'Claude-3-5-Sonnet-20240620', 'value': 'claude-3-5-sonnet-20240620'},
                {'name': 'Claude-3-Opus-20240229', 'value': 'claude-3-opus-20240229'},
                {'name': 'Claude-3-Sonnet-20240229', 'value': 'claude-3-sonnet-20240229'},
                {'name': 'Claude-3-Haiku-20240307', 'value': 'claude-3-haiku-20240307'},
                {'name': 'Claude-2.1', 'value': 'claude-2.1'},
                {'name': 'Claude-2.0', 'value': 'claude-2.0'},
            ],
            'description': 'Anthropic model to use',
        },
        {
            'displayName': 'Stream',
            'name': 'stream',
            'type': 'boolean',
            'default': False,
            'description': 'Stream the response',
        },
        {
            'displayName': 'System Message',
            'name': 'system_message',
            'type': 'string',
            'default': '',
            'description': 'System message for the model',
        },
        {
            'displayName': 'Temperature',
            'name': 'temperature',
            'type': 'string',
            'default': 0.1,
            'description': 'Controls randomness (0.0 to 1.0)',
        },
    ]
    inputs = {
        "model_name": {
            "type": "dropdown",
            "default": "claude-3-5-sonnet-20240620",
            "options": [
                "claude-3-5-sonnet-20240620",
                "claude-3-opus-20240229",
                "claude-3-sonnet-20240229",
                "claude-3-haiku-20240307",
                "claude-2.1",
                "claude-2.0"
            ],
            "description": "Anthropic model to use"
        },
        "anthropic_api_key": {
            "type": "string",
            "optional": True,
            "description": "Anthropic API key (overrides credential)"
        },
        "max_tokens": {
            "type": "number",
            "default": 4096,
            "description": "Maximum number of tokens to generate"
        },
        "temperature": {
            "type": "number",
            "default": 0.1,
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
        },
        "input_value": {
            "type": "string",
            "optional": True,
            "description": "User message or input text"
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
                from langchain_anthropic import ChatAnthropic
                from langchain_core.messages import HumanMessage, SystemMessage
            except ImportError:
                return {
                    "status": "error",
                    "error": "langchain-anthropic not installed. Run: pip install langchain-anthropic"
                }

            # Get credentials
            creds = await self.get_credential("anthropic_auth")
            api_key = creds.get("api_key") if creds else self.get_config("anthropic_api_key")
            
            if not api_key:
                return {"status": "error", "error": "Anthropic API Key is required"}

            # Get configuration
            model_name = self.get_config("model_name", "claude-3-5-sonnet-20240620")
            max_tokens = int(self.get_config("max_tokens", 4096))
            temperature = float(self.get_config("temperature", 0.1))
            system_msg = self.get_config("system_message")
            stream = self.get_config("stream", False)

            # Initialize model
            llm = ChatAnthropic(
                model=model_name,
                api_key=api_key,
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
                "error": f"Anthropic Model failed: {str(e)}"
            }

    async def get_langchain_object(self, context: Optional[Dict[str, Any]] = None) -> Any:
        """Helper to get the model object directly."""
        result = await self.execute(None, context)
        if result["status"] == "success":
            return result["data"]["model"]
        raise ValueError(result.get("error", "Unknown error"))