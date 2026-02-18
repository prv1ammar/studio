"""
LM Studio Node - Studio Standard (Universal Method)
Batch 118: AI Essentials & Local Inference
"""
from typing import Any, Dict, Optional, List
import aiohttp
from ..base import BaseNode
from ..registry import register_node

@register_node("lmstudio_node")
class LMStudioNode(BaseNode):
    """
    Generate text using LM Studio Local LLMs (OpenAI-compatible local server).
    """
    node_type = "lmstudio_node"
    version = "1.0.0"
    category = "ai"
    credentials_required = []


    properties = [
        {
            'displayName': 'Base Url',
            'name': 'base_url',
            'type': 'string',
            'default': 'http://localhost:1234/v1',
            'description': 'LM Studio server URL',
        },
        {
            'displayName': 'Max Tokens',
            'name': 'max_tokens',
            'type': 'string',
            'default': 1024,
        },
        {
            'displayName': 'Model Name',
            'name': 'model_name',
            'type': 'string',
            'default': '',
            'description': 'Model ID as loaded in LM Studio',
            'required': True,
        },
        {
            'displayName': 'Prompt',
            'name': 'prompt',
            'type': 'string',
            'default': '',
            'description': 'The prompt to send to the model',
            'required': True,
        },
        {
            'displayName': 'Temperature',
            'name': 'temperature',
            'type': 'string',
            'default': 0.1,
        },
    ]
    inputs = {
        "model_name": {
            "type": "string",
            "required": True,
            "description": "Model ID as loaded in LM Studio"
        },
        "prompt": {
            "type": "string",
            "required": True,
            "description": "The prompt to send to the model"
        },
        "base_url": {
            "type": "string",
            "default": "http://localhost:1234/v1",
            "description": "LM Studio server URL"
        },
        "temperature": {
            "type": "number",
            "default": 0.1
        },
        "max_tokens": {
            "type": "number",
            "default": 1024
        }
    }

    outputs = {
        "text": {"type": "string"},
        "raw": {"type": "dict"},
        "status": {"type": "string"}
    }

    async def execute(self, input_data: Any, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        try:
            model = self.get_config("model_name")
            prompt = self.get_config("prompt") or str(input_data)
            base_url = self.get_config("base_url", "http://localhost:1234/v1").rstrip('/')
            
            url = f"{base_url}/chat/completions"
            headers = {
                "Content-Type": "application/json"
            }
            payload = {
                "model": model,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": self.get_config("temperature", 0.1),
                "max_tokens": int(self.get_config("max_tokens", 1024))
            }

            async with aiohttp.ClientSession() as session:
                async with session.post(url, headers=headers, json=payload) as response:
                    if response.status != 200:
                        text = await response.text()
                        return {"status": "error", "error": f"LM Studio error {response.status}: {text}"}
                    
                    data = await response.json()
            
            text = data.get("choices", [{}])[0].get("message", {}).get("content", "")
            return {
                "status": "success",
                "data": {
                    "text": text,
                    "raw": data
                }
            }

        except Exception as e:
            return {"status": "error", "error": f"LM Studio Node Failed: {str(e)}"}