from typing import Any, Dict, Optional
from ..base import BaseNode
from ..registry import register_node
import os

@register_node("anthropicNode")
class AnthropicNode(BaseNode):
    """
    Official Anthropic Claude Node implementation.
    Executes standard Anthropic chat completions.
    """
    node_type = "anthropic_chat"
    version = "1.0.0"
    category = "ai"
    inputs = {
        "model": {"type": "string", "default": "claude-3-sonnet-20240229"},
        "temperature": {"type": "number", "default": 0.7},
        "max_tokens": {"type": "number", "default": 1000},
        "system_message": {"type": "string", "default": "You are a helpful AI assistant."},
        "input": {"type": "string", "description": "User prompt"}
    }
    outputs = {
        "text": {"type": "string", "description": "Generated response"},
        "status": {"type": "string"}
    }
    credentials_required = ["anthropic_api_key"]

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)

    async def execute(self, input_data: Any, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        try:
            from anthropic import AsyncAnthropic
            
            # 1. Try Secrets Manager
            creds = await self.get_credential("credentials_id")
            api_key = creds.get("api_key") if creds else None
            
            # 2. Fallback to config or ENV
            if not api_key:
                api_key = self.get_config("api_key") or os.getenv("ANTHROPIC_API_KEY")
                
            if not api_key:
                return {"status": "error", "error": "API Key is required for Anthropic Node"}
                
            model = self.get_config("model", "claude-3-sonnet-20240229")
            temperature = float(self.get_config("temperature", 0.7))
            max_tokens = int(self.get_config("max_tokens", 1000))
            system_message = self.get_config("system_message", "You are a helpful AI assistant.")
            
            # Helper to handle input being passed directly or config
            user_input = input_data if input_data else self.config.get("input", "")
            if not user_input:
                return {"status": "error", "error": "No input provided to Anthropic Node"}

            # Create client
            client = AsyncAnthropic(api_key=api_key)
            
            # Anthropic API structure
            response = await client.messages.create(
                model=model,
                max_tokens=max_tokens,
                temperature=temperature,
                system=system_message,
                messages=[
                    {"role": "user", "content": str(user_input)}
                ]
            )
            
            result = response.content[0].text
            return {"status": "success", "data": {"text": result}}
            
        except ImportError:
            return {"status": "error", "error": "Error: 'anthropic' package not installed. Please run: pip install anthropic"}
        except Exception as e:
            return {"status": "error", "error": f"Anthropic Execution Error: {str(e)}"}
