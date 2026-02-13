"""
Luma AI Video Generation Node - Studio Standard
Batch 53: Advanced AI (Visual & Generative)
"""
from typing import Any, Dict, Optional
import aiohttp
import asyncio
from ...base import BaseNode
from ...registry import register_node

@register_node("luma_video_node")
class LumaVideoNode(BaseNode):
    """
    Generate high-fidelity videos using Luma AI Dream Machine.
    Supports Text-to-Video and Image-to-Video.
    """
    node_type = "luma_video_node"
    version = "1.0.0"
    category = "media"
    credentials_required = ["luma_auth"]

    inputs = {
        "prompt": {
            "type": "string",
            "required": True,
            "description": "Video description or story"
        },
        "image_url": {
            "type": "string",
            "optional": True,
            "description": "Starting image for Image-to-Video generation"
        },
        "aspect_ratio": {
            "type": "dropdown",
            "default": "16:9",
            "options": ["16:9", "9:16", "1:1", "4:3", "3:4"],
            "description": "Output video aspect ratio"
        },
        "loop": {
            "type": "boolean",
            "default": False,
            "description": "Create a seamless looping video"
        },
        "wait_for_completion": {
            "type": "boolean",
            "default": True,
            "description": "Wait for the video to be rendered (can take minutes)"
        }
    }

    outputs = {
        "video_url": {"type": "string"},
        "generation_id": {"type": "string"},
        "status": {"type": "string"}
    }

    async def execute(self, input_data: Any, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        try:
            # 1. Resolve Auth
            creds = await self.get_credential("luma_auth")
            api_key = creds.get("api_key") if creds else self.get_config("api_key")
            
            if not api_key:
                return {"status": "error", "error": "Luma AI API Key is required."}

            prompt = self.get_config("prompt")
            # Dynamic Override
            if isinstance(input_data, str) and input_data.startswith("http"):
                image_url = input_data
                prompt = prompt or "Natural movement and cinematic lighting"
            elif isinstance(input_data, str):
                prompt = input_data
                image_url = self.get_config("image_url")
            else:
                image_url = self.get_config("image_url")

            if not prompt:
                return {"status": "error", "error": "Prompt is required for video generation."}

            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "prompt": prompt,
                "aspect_ratio": self.get_config("aspect_ratio", "16:9"),
                "loop": self.get_config("loop", False)
            }
            if image_url:
                payload["keyframes"] = {
                    "frame0": {
                        "type": "image",
                        "url": image_url
                    }
                }

            async with aiohttp.ClientSession() as session:
                # 2. Start Generation
                async with session.post("https://api.lumalabs.ai/dream-machine/v1/generations", headers=headers, json=payload) as resp:
                    if resp.status >= 400:
                        err_text = await resp.text()
                        return {"status": "error", "error": f"Luma API Error: {err_text}"}
                    
                    gen_data = await resp.json()
                    gen_id = gen_data.get("id")

                if not self.get_config("wait_for_completion", True):
                    return {
                        "status": "success",
                        "data": {
                            "generation_id": gen_id,
                            "status": "queued",
                            "video_url": None
                        }
                    }

                # 3. Polling for Result
                max_retries = 60 # 5 minutes roughly
                for i in range(max_retries):
                    async with session.get(f"https://api.lumalabs.ai/dream-machine/v1/generations/{gen_id}", headers=headers) as resp:
                        status_data = await resp.json()
                        state = status_data.get("state")
                        
                        if state == "completed":
                            video_url = status_data.get("assets", {}).get("video")
                            return {
                                "status": "success",
                                "data": {
                                    "video_url": video_url,
                                    "generation_id": gen_id,
                                    "status": "completed"
                                }
                            }
                        elif state == "failed":
                            return {"status": "error", "error": f"Luma Rendering Failed: {status_data.get('failure_reason')}"}
                        
                        await asyncio.sleep(5)

                return {
                    "status": "success",
                    "data": {
                        "generation_id": gen_id,
                        "status": "timeout_polling",
                        "info": "Video is still rendering. Check the generation_id later."
                    }
                }

        except Exception as e:
            return {"status": "error", "error": f"Luma Video Node Failed: {str(e)}"}
