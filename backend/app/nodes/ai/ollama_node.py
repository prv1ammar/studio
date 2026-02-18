"""
Ollama Node - Studio Standard (Universal Method)
Batch 114: Advanced AI Frameworks & Memory
"""
from typing import Any, Dict, Optional, List
import aiohttp
import json
from ..base import BaseNode
from ..registry import register_node

@register_node("ollama_node")
class OllamaNode(BaseNode):
    """
    Generate text using Ollama Local LLMs.
    """
    node_type = "ollama_node"
    version = "1.0.0"
    category = "ai"
    credentials_required = []


    properties = [
        {
            'displayName': 'Base Url',
            'name': 'base_url',
            'type': 'string',
            'default': 'http://localhost:11434',
            'description': 'Ollama API URL',
        },
        {
            'displayName': 'Json Mode',
            'name': 'json_mode',
            'type': 'boolean',
            'default': False,
            'description': 'Enable JSON output mode',
        },
        {
            'displayName': 'Model Name',
            'name': 'model_name',
            'type': 'string',
            'default': '',
            'description': 'Model name (e.g., llama3, mistral)',
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
            'displayName': 'Stream',
            'name': 'stream',
            'type': 'boolean',
            'default': False,
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
            "description": "Model name (e.g., llama3, mistral)"
        },
        "prompt": {
            "type": "string",
            "required": True,
            "description": "The prompt to send to the model"
        },
        "base_url": {
            "type": "string",
            "default": "http://localhost:11434",
            "description": "Ollama API URL"
        },
        "temperature": {
            "type": "number",
            "default": 0.1
        },
        "stream": {
            "type": "boolean",
            "default": False
        },
        "json_mode": {
            "type": "boolean",
            "default": False,
            "description": "Enable JSON output mode"
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
            base_url = self.get_config("base_url", "http://localhost:11434").rstrip('/')
            
            url = f"{base_url}/api/generate"
            payload = {
                "model": model,
                "prompt": prompt,
                "stream": self.get_config("stream", False),
                "options": {
                    "temperature": self.get_config("temperature", 0.1)
                }
            }
            
            if self.get_config("json_mode"):
                payload["format"] = "json"

            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=payload) as response:
                    if response.status != 200:
                        text = await response.text()
                        return {"status": "error", "error": f"Ollama error {response.status}: {text}"}
                    
                    data = await response.json()
                    
            return {
                "status": "success",
                "data": {
                    "text": data.get("response", ""),
                    "raw": data
                }
            }

        except Exception as e:
            return {"status": "error", "error": f"Ollama Node Failed: {str(e)}"}