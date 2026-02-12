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
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.node_type = "anthropic_chat"

    async def execute(self, input_data: Any, context: Optional[Dict[str, Any]] = None) -> str:
        try:
            from anthropic import AsyncAnthropic
            
            # 1. Try Secrets Manager
            creds = await self.get_credential("credentials_id")
            api_key = creds.get("api_key") if creds else None
            
            # 2. Fallback to config or ENV
            if not api_key:
                api_key = self.get_config("api_key") or os.getenv("ANTHROPIC_API_KEY")
                
            if not api_key:
                return "Error: API Key is required for Anthropic Node"
                
            model = self.get_config("model", "claude-3-sonnet-20240229")
            temperature = float(self.get_config("temperature", 0.7))
            max_tokens = int(self.get_config("max_tokens", 1000))
            system_message = self.get_config("system_message", "You are a helpful AI assistant.")
            
            # Helper to handle input being passed directly or config
            user_input = input_data if input_data else self.config.get("input", "")
            if not user_input:
                return "Error: No input provided to Anthropic Node"

            # Create client
            client = AsyncAnthropic(api_key=api_key)
            
            print(f"[AnthropicNode] Sending request to {model}...")
            
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
            print(f"[AnthropicNode] Received response: {result[:50]}...")
            return result
            
        except ImportError:
            return "Error: 'anthropic' package not installed. Please run: pip install anthropic"
        except Exception as e:
            print(f"[AnthropicNode] Error: {e}")
            return f"Anthropic Execution Error: {str(e)}"
