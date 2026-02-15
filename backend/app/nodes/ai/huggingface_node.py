"""
Hugging Face Node - Studio Standard (Universal Method)
Batch 118: AI Essentials & Local Inference
"""
from typing import Any, Dict, Optional, List
import aiohttp
from ...base import BaseNode
from ...registry import register_node

@register_node("huggingface_node")
class HuggingFaceNode(BaseNode):
    """
    Generate text or embeddings using Hugging Face Inference API.
    """
    node_type = "huggingface_node"
    version = "1.0.0"
    category = "ai"
    credentials_required = ["huggingface_auth"]

    inputs = {
        "model_id": {
            "type": "string",
            "required": True,
            "description": "Hugging Face model ID (e.g. 'gpt2' or 'facebook/bart-large-cnn')"
        },
        "inputs": {
            "type": "string",
            "required": True,
            "description": "Input text for the model"
        },
        "task": {
            "type": "dropdown",
            "default": "text-generation",
            "options": ["text-generation", "summarization", "translation", "feature-extraction"],
            "description": "The task to perform"
        }
    }

    outputs = {
        "result": {"type": "any"},
        "status": {"type": "string"}
    }

    async def execute(self, input_data: Any, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        try:
            creds = await self.get_credential("huggingface_auth")
            api_key = creds.get("api_key")
            
            if not api_key:
                return {"status": "error", "error": "Hugging Face API Key is required"}

            model_id = self.get_config("model_id")
            inputs = self.get_config("inputs") or str(input_data)
            
            url = f"https://api-inference.huggingface.co/models/{model_id}"
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            }
            payload = {"inputs": inputs}

            async with aiohttp.ClientSession() as session:
                async with session.post(url, headers=headers, json=payload) as response:
                    if response.status != 200:
                        text = await response.text()
                        return {"status": "error", "error": f"Hugging Face error {response.status}: {text}"}
                    
                    data = await response.json()

            return {
                "status": "success",
                "data": {
                    "result": data
                }
            }

        except Exception as e:
            return {"status": "error", "error": f"Hugging Face Node Failed: {str(e)}"}
