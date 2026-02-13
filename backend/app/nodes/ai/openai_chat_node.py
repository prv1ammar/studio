"""
OpenAI Chat Node - Studio Standard (Universal Method)
Batch 100: AI & LLM (The Grande Finale)
"""
from typing import Any, Dict, Optional, List
import aiohttp
import json
from ...base import BaseNode
from ...registry import register_node

@register_node("openai_chat_node")
class OpenAIChatNode(BaseNode):
    """
    Generate chat completions using OpenAI's GPT models (GPT-4o, GPT-3.5, etc).
    """
    node_type = "openai_chat_node"
    version = "1.0.0"
    category = "ai"
    credentials_required = ["openai_auth"]

    inputs = {
        "model": {
            "type": "dropdown",
            "default": "gpt-4o",
            "options": ["gpt-4o", "gpt-4-turbo", "gpt-3.5-turbo"],
            "description": "Model to use"
        },
        "system_message": {
            "type": "string",
            "default": "You are a helpful assistant.",
            "description": "System context"
        },
        "user_message": {
            "type": "string",
            "required": True,
            "description": "User prompt"
        },
        "max_tokens": {
            "type": "number",
            "default": 1000,
            "description": "Max tokens to generate"
        },
        "temperature": {
            "type": "number",
            "default": 0.7,
            "description": "Randomness (0.0 to 2.0)"
        }
    }

    outputs = {
        "result": {"type": "any"},
        "text": {"type": "string"},
        "status": {"type": "string"}
    }

    async def execute(self, input_data: Any, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        try:
            # 1. Authentication
            creds = await self.get_credential("openai_auth")
            api_key = creds.get("api_key")
            base_url = creds.get("base_url", "https://api.openai.com/v1")
            
            if not api_key:
                return {"status": "error", "error": "OpenAI API Key required."}

            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            }
            
            # 2. Prepare Payload
            model = self.get_config("model", "gpt-4o")
            system_msg = self.get_config("system_message", "You are a helpful assistant.")
            user_msg = self.get_config("user_message") or str(input_data)
            max_tokens = int(self.get_config("max_tokens", 1000))
            temperature = float(self.get_config("temperature", 0.7))

            messages = [
                {"role": "system", "content": system_msg},
                {"role": "user", "content": user_msg}
            ]

            payload = {
                "model": model,
                "messages": messages,
                "max_tokens": max_tokens,
                "temperature": temperature
            }

            # 3. Connect to Real API
            url = f"{base_url}/chat/completions"

            async with aiohttp.ClientSession() as session:
                async with session.post(url, headers=headers, json=payload) as resp:
                    if resp.status != 200:
                        error_text = await resp.text()
                        return {"status": "error", "error": f"OpenAI API Error: {resp.status} - {error_text}"}
                    
                    res_data = await resp.json()
                    
                    # Extract content
                    choice = res_data.get("choices", [])[0]
                    content = choice.get("message", {}).get("content", "")
                    
                    return {
                        "status": "success",
                        "data": {
                            "result": res_data,
                            "text": content
                        }
                    }

        except Exception as e:
            return {"status": "error", "error": f"OpenAI Node Failed: {str(e)}"}
