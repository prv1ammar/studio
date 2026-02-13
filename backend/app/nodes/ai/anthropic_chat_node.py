"""
Anthropic Chat Node - Studio Standard (Universal Method)
Batch 100: AI & LLM (The Grande Finale)
"""
from typing import Any, Dict, Optional, List
import aiohttp
import json
from ...base import BaseNode
from ...registry import register_node

@register_node("anthropic_chat_node")
class AnthropicChatNode(BaseNode):
    """
    Generate chat completions using Anthropic's Claude models.
    """
    node_type = "anthropic_chat_node"
    version = "1.0.0"
    category = "ai"
    credentials_required = ["anthropic_auth"]

    inputs = {
        "model": {
            "type": "dropdown",
            "default": "claude-3-5-sonnet-20240620",
            "options": ["claude-3-5-sonnet-20240620", "claude-3-opus-20240229", "claude-3-haiku-20240307"],
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
            "default": 1024,
            "description": "Max output tokens"
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
            creds = await self.get_credential("anthropic_auth")
            api_key = creds.get("api_key")
            
            if not api_key:
                return {"status": "error", "error": "Anthropic API Key required."}

            headers = {
                "x-api-key": api_key,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json"
            }
            
            # 2. Prepare Payload
            model = self.get_config("model", "claude-3-5-sonnet-20240620")
            system_msg = self.get_config("system_message", "You are a helpful assistant.")
            user_msg = self.get_config("user_message") or str(input_data)
            max_tokens = int(self.get_config("max_tokens", 1024))
            
            messages = [
                {"role": "user", "content": user_msg}
            ]
            
            payload = {
                "model": model,
                "max_tokens": max_tokens,
                "messages": messages,
                "system": system_msg
            }
            
            # 3. Connect to Real API
            url = "https://api.anthropic.com/v1/messages"
            
            async with aiohttp.ClientSession() as session:
                async with session.post(url, headers=headers, json=payload) as resp:
                    if resp.status != 200:
                        error_text = await resp.text()
                        return {"status": "error", "error": f"Anthropic API Error: {resp.status} - {error_text}"}
                    
                    res_data = await resp.json()
                    
                    content = res_data.get("content", [])
                    extracted_text = ""
                    for block in content:
                        if block["type"] == "text":
                            extracted_text += block["text"]
                    
                    return {
                        "status": "success",
                        "data": {
                            "result": res_data,
                            "text": extracted_text
                        }
                    }

        except Exception as e:
            return {"status": "error", "error": f"Anthropic Node Failed: {str(e)}"}
