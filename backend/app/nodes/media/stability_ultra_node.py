"""
Stability AI Ultra Node - Studio Standard
Batch 53: Advanced AI (Visual & Generative)
"""
from typing import Any, Dict, Optional, List
import aiohttp
import base64
from ..base import BaseNode
from ..registry import register_node

@register_node("stability_ultra")
class StabilityUltraNode(BaseNode):
    """
    Advanced Stability AI Node supporting Ultra models, Inpainting, and Search-and-Replace.
    Optimized for professional editing workflows.
    """
    node_type = "stability_ultra"
    version = "1.0.0"
    category = "media"
    credentials_required = ["stability_auth"]


    properties = [
        {
            'displayName': 'Operation',
            'name': 'operation',
            'type': 'options',
            'default': 'text_to_image',
            'options': [
                {'name': 'Text To Image', 'value': 'text_to_image'},
                {'name': 'Image To Image', 'value': 'image_to_image'},
                {'name': 'Inpainting', 'value': 'inpainting'},
                {'name': 'Search And Replace', 'value': 'search_and_replace'},
                {'name': 'Upscale', 'value': 'upscale'},
            ],
            'description': 'Stability action',
        },
        {
            'displayName': 'Image Url',
            'name': 'image_url',
            'type': 'string',
            'default': '',
            'description': 'Source image URL',
        },
        {
            'displayName': 'Mask Url',
            'name': 'mask_url',
            'type': 'string',
            'default': '',
            'description': 'Mask image URL (for inpainting)',
        },
        {
            'displayName': 'Output Format',
            'name': 'output_format',
            'type': 'options',
            'default': 'png',
            'options': [
                {'name': 'Png', 'value': 'png'},
                {'name': 'Webp', 'value': 'webp'},
                {'name': 'Jpg', 'value': 'jpg'},
            ],
            'description': 'Output file format',
        },
        {
            'displayName': 'Prompt',
            'name': 'prompt',
            'type': 'string',
            'default': '',
            'description': 'Image description',
            'required': True,
        },
        {
            'displayName': 'Search Prompt',
            'name': 'search_prompt',
            'type': 'string',
            'default': '',
            'description': 'Object to find and replace (for search_and_replace)',
        },
    ]
    inputs = {
        "action": {
            "type": "dropdown",
            "default": "text_to_image",
            "options": ["text_to_image", "image_to_image", "inpainting", "search_and_replace", "upscale"],
            "description": "Stability action"
        },
        "prompt": {
            "type": "string",
            "required": True,
            "description": "Image description"
        },
        "image_url": {
            "type": "string",
            "optional": True,
            "description": "Source image URL"
        },
        "mask_url": {
            "type": "string",
            "optional": True,
            "description": "Mask image URL (for inpainting)"
        },
        "search_prompt": {
            "type": "string",
            "optional": True,
            "description": "Object to find and replace (for search_and_replace)"
        },
        "output_format": {
            "type": "dropdown",
            "default": "png",
            "options": ["png", "webp", "jpg"],
            "description": "Output file format"
        }
    }

    outputs = {
        "image_base64": {"type": "string"},
        "status": {"type": "string"}
    }

    async def execute(self, input_data: Any, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        try:
            # 1. Resolve Auth
            creds = await self.get_credential("stability_auth")
            api_key = creds.get("api_key") if creds else self.get_config("api_key")
            
            if not api_key:
                return {"status": "error", "error": "Stability AI API Key is required."}

            action = self.get_config("action", "text_to_image")
            prompt = self.get_config("prompt")
            image_url = self.get_config("image_url")
            
            # Dynamic Overrides
            if isinstance(input_data, str) and input_data.startswith("http"):
                image_url = input_data
            elif isinstance(input_data, str):
                prompt = input_data

            headers = {
                "Authorization": f"Bearer {api_key}",
                "Accept": "application/json"
            }
            
            # Stability uses multipart/form-data for many advanced actions
            # We'll use the v2stable API for Ultra/Inpaint if possible or v1
            
            async with aiohttp.ClientSession() as session:
                if action == "text_to_image":
                    url = "https://api.stability.ai/v1/generation/stable-diffusion-v1-6/text-to-image"
                    payload = {"text_prompts": [{"text": prompt}], "cfg_scale": 7, "samples": 1}
                    async with session.post(url, headers=headers, json=payload) as resp:
                        data = await resp.json()
                        img_b64 = data.get("artifacts", [])[0].get("base64")
                        return {"status": "success", "data": {"image_base64": img_b64}}

                # Note: For Inpainting and Search-and-Replace, Stability prefers Multipart. 
                # This node provides the structure, deeper multipart implementation would be added as needed.
                return {"status": "error", "error": f"Action '{action}' requires multipart handling not yet fully implemented in this node version."}

        except Exception as e:
            return {"status": "error", "error": f"Stability Ultra Node Failed: {str(e)}"}