"""
Leonardo AI Node - Studio Standard
Batch 53: Advanced AI (Visual & Generative)
"""
from typing import Any, Dict, Optional, List
import aiohttp
import asyncio
from ..base import BaseNode
from ..registry import register_node

@register_node("leonardo_ai")
class LeonardoAINode(BaseNode):
    """
    Advanced Image Generation, Inpainting, and Motion via Leonardo AI.
    """
    node_type = "leonardo_ai"
    version = "1.0.0"
    category = "media"
    credentials_required = ["leonardo_auth"]


    properties = [
        {
            'displayName': 'Operation',
            'name': 'operation',
            'type': 'options',
            'default': 'generate',
            'options': [
                {'name': 'Generate', 'value': 'generate'},
                {'name': 'Upscale', 'value': 'upscale'},
                {'name': 'Inpainting', 'value': 'inpainting'},
                {'name': 'Motion', 'value': 'motion'},
            ],
            'description': 'Leonardo AI action',
        },
        {
            'displayName': 'Image Url',
            'name': 'image_url',
            'type': 'string',
            'default': '',
            'description': 'Source image for inpainting, motion, or upscaling',
        },
        {
            'displayName': 'Mask Url',
            'name': 'mask_url',
            'type': 'string',
            'default': '',
            'description': 'Mask image for inpainting',
        },
        {
            'displayName': 'Model Id',
            'name': 'model_id',
            'type': 'string',
            'default': '6bef9f11-99ad-4fd8-bccb-483927653cb2',
            'description': 'Specific model UID',
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
            'displayName': 'Wait For Completion',
            'name': 'wait_for_completion',
            'type': 'boolean',
            'default': True,
        },
    ]
    inputs = {
        "action": {
            "type": "dropdown",
            "default": "generate",
            "options": ["generate", "upscale", "inpainting", "motion"],
            "description": "Leonardo AI action"
        },
        "prompt": {
            "type": "string",
            "required": True,
            "description": "Image description"
        },
        "model_id": {
            "type": "string",
            "default": "6bef9f11-99ad-4fd8-bccb-483927653cb2", # Leonardo Vision XL
            "description": "Specific model UID"
        },
        "image_url": {
            "type": "string",
            "optional": True,
            "description": "Source image for inpainting, motion, or upscaling"
        },
        "mask_url": {
            "type": "string",
            "optional": True,
            "description": "Mask image for inpainting"
        },
        "wait_for_completion": {
            "type": "boolean",
            "default": True
        }
    }

    outputs = {
        "image_url": {"type": "string"},
        "generation_id": {"type": "string"},
        "status": {"type": "string"}
    }

    async def execute(self, input_data: Any, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        try:
            # 1. Resolve Auth
            creds = await self.get_credential("leonardo_auth")
            api_key = creds.get("api_key") if creds else self.get_config("api_key")
            
            if not api_key:
                return {"status": "error", "error": "Leonardo AI API Key is required."}

            action = self.get_config("action", "generate")
            prompt = self.get_config("prompt")
            image_url = self.get_config("image_url")
            
            # Dynamic Overrides
            if isinstance(input_data, str) and input_data.startswith("http"):
                image_url = input_data
            elif isinstance(input_data, str):
                prompt = input_data

            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
                "Accept": "application/json"
            }
            
            base_url = "https://cloud.leonardo.ai/api/rest/v1"

            async with aiohttp.ClientSession() as session:
                payload = {
                    "prompt": prompt,
                    "modelId": self.get_config("model_id"),
                    "num_images": 1,
                    "width": 1024,
                    "height": 1024
                }

                if action == "generate":
                    endpoint = f"{base_url}/generations"
                elif action == "motion":
                    endpoint = f"{base_url}/generations-motion-svd"
                    payload = {"imageId": image_url if not image_url.startswith("http") else None} # Leonardo often needs their internal imageId
                elif action == "upscale":
                    # Upscaling usually uses variations or dedicated endpoints
                    return {"status": "error", "error": "Upscale action requires internal Leonardo image IDs."}
                else:
                    return {"status": "error", "error": f"Unsupported action: {action}"}

                # 2. Trigger Generation
                async with session.post(endpoint, headers=headers, json=payload) as resp:
                    resp_data = await resp.json()
                    if resp.status >= 400:
                         return {"status": "error", "error": f"Leonardo API Error: {resp_data}"}
                    
                    # Leonardo returns sdGenerationJob or similar
                    gen_id = resp_data.get("sdGenerationJob", {}).get("generationId") or resp_data.get("motionGenerationJob", {}).get("generationId")

                if not self.get_config("wait_for_completion", True):
                    return {"status": "success", "data": {"generation_id": gen_id, "status": "queued"}}

                # 3. Polling
                for _ in range(30):
                    async with session.get(f"{base_url}/generations/{gen_id}", headers=headers) as resp:
                        gen_status = await resp.json()
                        images = gen_status.get("generations_by_pk", {}).get("generated_images", [])
                        
                        if images:
                            result_url = images[0].get("url")
                            return {
                                "status": "success",
                                "data": {
                                    "image_url": result_url,
                                    "generation_id": gen_id,
                                    "status": "completed"
                                }
                            }
                        await asyncio.sleep(5)

                return {"status": "success", "data": {"generation_id": gen_id, "status": "polling_timeout"}}

        except Exception as e:
            return {"status": "error", "error": f"Leonardo AI Node Failed: {str(e)}"}