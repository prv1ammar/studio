"""
HuggingFace Inference Node - Studio Standard (Universal Method)
Batch 100: AI & LLM (The Grande Finale)
"""
from typing import Any, Dict, Optional, List
import aiohttp
import json
from ...base import BaseNode
from ...registry import register_node

@register_node("huggingface_inference_node")
class HuggingFaceInferenceNode(BaseNode):
    """
    Run inference on HuggingFace models using the Inference API.
    """
    node_type = "huggingface_inference_node"
    version = "1.0.0"
    category = "ai"
    credentials_required = ["huggingface_auth"]

    inputs = {
        "model_id": {
            "type": "string",
            "required": True,
            "description": "Model ID (e.g. gpt2, facebook/bart-large-cnn)"
        },
        "task": {
            "type": "dropdown",
            "default": "text-generation",
            "options": ["text-generation", "summarization", "translation", "conversational", "fill-mask"],
            "description": "Task type"
        },
        "input_text": {
            "type": "string",
            "required": True,
            "description": "Input text"
        },
        "parameters": {
            "type": "string",
            "optional": True,
            "description": "JSON parameters (e.g. {max_new_tokens: 50})"
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
            creds = await self.get_credential("huggingface_auth")
            api_token = creds.get("api_token")
            
            if not api_token:
                return {"status": "error", "error": "HuggingFace API Token required."}

            headers = {
                "Authorization": f"Bearer {api_token}",
                "Content-Type": "application/json"
            }
            
            # 2. Prepare Payload
            model_id = self.get_config("model_id")
            if not model_id:
                return {"status": "error", "error": "model_id required"}
            
            input_text = self.get_config("input_text") or str(input_data)
            
            import json
            params_str = self.get_config("parameters", "{}")
            params = json.loads(params_str) if isinstance(params_str, str) else params_str
            
            payload = {"inputs": input_text, "parameters": params}
            
            # 3. Connect to Real API
            url = f"https://api-inference.huggingface.co/models/{model_id}"
            
            async with aiohttp.ClientSession() as session:
                async with session.post(url, headers=headers, json=payload) as resp:
                    if resp.status != 200:
                        error_text = await resp.text()
                        return {"status": "error", "error": f"HuggingFace API Error: {resp.status} - {error_text}"}
                    
                    res_data = await resp.json()
                    
                    # Extract result text (basic extraction, varies by task)
                    generated = ""
                    if isinstance(res_data, list) and len(res_data) > 0:
                        item = res_data[0]
                        if "generated_text" in item:
                            generated = item["generated_text"]
                        elif "summary_text" in item:
                            generated = item["summary_text"]
                        elif "translation_text" in item:
                            generated = item["translation_text"]
                        else:
                            generated = str(item)
                    elif isinstance(res_data, dict):
                         generated = res_data.get("generated_text", str(res_data))
                    
                    return {
                        "status": "success",
                        "data": {
                            "result": res_data,
                            "text": generated
                        }
                    }

        except Exception as e:
            return {"status": "error", "error": f"HuggingFace Node Failed: {str(e)}"}
