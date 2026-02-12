import aiohttp
from typing import Any, Dict, Optional
from ...base import BaseNode
from ...registry import register_node
import base64

@register_node("stability_image_gen")
class StabilityAINode(BaseNode):
    """Generates images using Stability AI models."""
    node_type = "stability_image_gen"
    version = "1.0.0"
    category = "media"
    credentials_required = ["stability_auth"]

    inputs = {
        "prompt": {"type": "string", "description": "Text description of the image"},
        "engine_id": {"type": "string", "default": "stable-diffusion-v1-6"},
        "width": {"type": "number", "default": 512},
        "height": {"type": "number", "default": 512},
        "samples": {"type": "number", "default": 1}
    }
    outputs = {
        "images": {"type": "list", "description": "List of base64 encoded images"},
        "status": {"type": "string"}
    }

    async def execute(self, input_data: Any, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        creds = await self.get_credential("stability_auth")
        api_key = creds.get("api_key") if creds else self.get_config("api_key")

        if not api_key:
            return {"status": "error", "error": "Stability AI API Key is required.", "data": None}

        prompt = input_data if isinstance(input_data, str) else self.get_config("prompt")
        if isinstance(input_data, dict):
            prompt = input_data.get("prompt") or input_data.get("text") or prompt
            
        if not prompt:
            return {"status": "error", "error": "Prompt is required for image generation.", "data": None}

        engine_id = self.get_config("engine_id", "stable-diffusion-v1-6")
        url = f"https://api.stability.ai/v1/generation/{engine_id}/text-to-image"
        
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Authorization": f"Bearer {api_key}"
        }
        
        payload = {
            "text_prompts": [{"text": prompt}],
            "cfg_scale": 7,
            "height": self.get_config("height", 512),
            "width": self.get_config("width", 512),
            "samples": self.get_config("samples", 1),
            "steps": 30,
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=payload, headers=headers) as resp:
                    if resp.status >= 400:
                        err_data = await resp.json()
                        return {"status": "error", "error": f"Stability AI API Error: {err_data.get('message')}", "data": err_data}
                    
                    data = await resp.json()
                    images = [img.get("base64") for img in data.get("artifacts", [])]
                    
                    return {
                        "status": "success",
                        "data": {
                            "images": images,
                            "count": len(images)
                        }
                    }
        except Exception as e:
            return {"status": "error", "error": f"Stability AI Node Failed: {str(e)}", "data": None}
