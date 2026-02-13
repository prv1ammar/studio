"""
OpenAI Dall-E Image Generation Node - Studio Standard
Batch 42: Image & Audio
"""
from typing import Any, Dict, Optional, List
from ...base import BaseNode
from ...registry import register_node

@register_node("dalle_image_gen")
class DallEImageGenNode(BaseNode):
    """
    Generate images from text prompts using OpenAI's DALL-E models.
    Supports DALL-E 3 and DALL-E 2.
    """
    node_type = "dalle_image_gen"
    version = "1.0.0"
    category = "media"
    credentials_required = ["openai_auth"]

    inputs = {
        "prompt": {
            "type": "string",
            "required": True,
            "description": "Image description prompt"
        },
        "model": {
            "type": "dropdown",
            "default": "dall-e-3",
            "options": ["dall-e-3", "dall-e-2"],
            "description": "Model version"
        },
        "size": {
            "type": "dropdown",
            "default": "1024x1024",
            "options": ["1024x1024", "1024x1792", "1792x1024", "512x512", "256x256"],
            "description": "Image resolution (availability depends on model)"
        },
        "quality": {
            "type": "dropdown",
            "default": "standard",
            "options": ["standard", "hd"],
            "description": "Quality mode (DALL-E 3 only)"
        },
        "style": {
            "type": "dropdown",
            "default": "vivid",
            "options": ["vivid", "natural"],
            "description": "Style mode (DALL-E 3 only)"
        },
        "n": {
            "type": "number",
            "default": 1,
            "description": "Number of images (DALL-E 2 only)"
        }
    }

    outputs = {
        "image_url": {"type": "string"},
        "revised_prompt": {"type": "string"}
    }

    async def execute(self, input_data: Any, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        try:
            # Check dependency
            try:
                from openai import AsyncOpenAI
            except ImportError:
                return {"status": "error", "error": "openai not installed. Run: pip install openai"}

            # Get Creds
            creds = await self.get_credential("openai_auth")
            api_key = creds.get("api_key") if creds else self.get_config("api_key") or self.get_config("openai_api_key")
            
            if not api_key:
                return {"status": "error", "error": "OpenAI API Key is required."}

            client = AsyncOpenAI(api_key=api_key)
            
            # Get Config
            prompt = self.get_config("prompt")
            # Override from input
            if isinstance(input_data, str) and input_data:
                prompt = input_data
            elif isinstance(input_data, dict):
                prompt = input_data.get("prompt") or input_data.get("text") or prompt

            if not prompt:
                return {"status": "error", "error": "Prompt is required."}

            model = self.get_config("model", "dall-e-3")
            size = self.get_config("size", "1024x1024")
            quality = self.get_config("quality", "standard")
            style = self.get_config("style", "vivid")
            n = int(self.get_config("n", 1))

            # DALL-E 3 constraints
            if model == "dall-e-3":
                n = 1 # DALL-E 3 only supports n=1 currently via API
                if size not in ["1024x1024", "1024x1792", "1792x1024"]:
                    size = "1024x1024" # Fallback to supported size
            
            # Construct params
            params = {
                "model": model,
                "prompt": prompt,
                "size": size,
                "n": n,
            }

            if model == "dall-e-3":
                params["quality"] = quality
                params["style"] = style

            response = await client.images.generate(**params)
            
            # Extract results
            # Return first image URL as primary output
            first_image = response.data[0]
            
            return {
                "status": "success",
                "data": {
                    "image_url": first_image.url,
                    "revised_prompt": getattr(first_image, "revised_prompt", prompt),
                    "created": response.created,
                    "all_images": [img.url for img in response.data]
                }
            }

        except Exception as e:
            return {"status": "error", "error": f"DALL-E Generation Failed: {str(e)}"}
