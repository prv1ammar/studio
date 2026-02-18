"""
Perplexity Node - Studio Standard (Universal Method)
Batch 114: Advanced AI Frameworks & Memory
"""
from typing import Any, Dict, Optional
import aiohttp
from ..base import BaseNode
from ..registry import register_node

@register_node("perplexity_node")
class PerplexityNode(BaseNode):
    """
    Generate text using Perplexity LLMs (Search-optimized AI).
    """
    node_type = "perplexity_node"
    version = "1.0.0"
    category = "ai"
    credentials_required = ["perplexity_auth"]


    properties = [
        {
            'displayName': 'Model Name',
            'name': 'model_name',
            'type': 'options',
            'default': 'llama-3.1-sonar-small-128k-online',
            'options': [
                {'name': 'Llama-3.1-Sonar-Small-128K-Online', 'value': 'llama-3.1-sonar-small-128k-online'},
                {'name': 'Llama-3.1-Sonar-Large-128K-Online', 'value': 'llama-3.1-sonar-large-128k-online'},
                {'name': 'Llama-3.1-Sonar-Huge-128K-Online', 'value': 'llama-3.1-sonar-huge-128k-online'},
                {'name': 'Llama-3.1-Sonar-Small-128K-Chat', 'value': 'llama-3.1-sonar-small-128k-chat'},
                {'name': 'Llama-3.1-Sonar-Large-128K-Chat', 'value': 'llama-3.1-sonar-large-128k-chat'},
            ],
            'description': 'Perplexity model to use',
        },
        {
            'displayName': 'Prompt',
            'name': 'prompt',
            'type': 'string',
            'default': '',
            'description': 'The search query or prompt',
            'required': True,
        },
    ]
    inputs = {
        "model_name": {
            "type": "dropdown",
            "default": "llama-3.1-sonar-small-128k-online",
            "options": [
                "llama-3.1-sonar-small-128k-online",
                "llama-3.1-sonar-large-128k-online",
                "llama-3.1-sonar-huge-128k-online",
                "llama-3.1-sonar-small-128k-chat",
                "llama-3.1-sonar-large-128k-chat"
            ],
            "description": "Perplexity model to use"
        },
        "prompt": {
            "type": "string",
            "required": True,
            "description": "The search query or prompt"
        }
    }

    outputs = {
        "text": {"type": "string"},
        "status": {"type": "string"}
    }

    async def execute(self, input_data: Any, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        try:
            creds = await self.get_credential("perplexity_auth")
            api_key = creds.get("api_key")
            
            if not api_key:
                return {"status": "error", "error": "Perplexity API Key is required"}

            model = self.get_config("model_name", "llama-3.1-sonar-small-128k-online")
            prompt = self.get_config("prompt") or str(input_data)

            url = "https://api.perplexity.ai/chat/completions"
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            }
            payload = {
                "model": model,
                "messages": [{"role": "user", "content": prompt}]
            }

            async with aiohttp.ClientSession() as session:
                async with session.post(url, headers=headers, json=payload) as response:
                    if response.status != 200:
                        return {"status": "error", "error": f"Perplexity error {response.status}"}
                    
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
            return {"status": "error", "error": f"Perplexity Node Failed: {str(e)}"}