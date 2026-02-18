"""
Heygen Node - Studio Standard
Batch 112: AI Video & Media
"""
from typing import Any, Dict, Optional
import aiohttp
from ..base import BaseNode
from ..registry import register_node

@register_node("heygen_node")
class HeygenNode(BaseNode):
    """
    Generate AI videos using Heygen's Avatar API.
    """
    node_type = "heygen_node"
    version = "1.0.0"
    category = "media"
    credentials_required = ["heygen_auth"]


    properties = [
        {
            'displayName': 'Operation',
            'name': 'operation',
            'type': 'options',
            'default': 'generate_video',
            'options': [
                {'name': 'Generate Video', 'value': 'generate_video'},
                {'name': 'Get Video Status', 'value': 'get_video_status'},
                {'name': 'List Avatars', 'value': 'list_avatars'},
                {'name': 'List Voices', 'value': 'list_voices'},
            ],
            'description': 'Heygen action',
        },
        {
            'displayName': 'Avatar Id',
            'name': 'avatar_id',
            'type': 'string',
            'default': 'Daisy_public_2_20230913',
            'description': 'The ID of the avatar to use',
        },
        {
            'displayName': 'Input Text',
            'name': 'input_text',
            'type': 'string',
            'default': '',
            'description': 'Text for the avatar to speak',
        },
        {
            'displayName': 'Video Id',
            'name': 'video_id',
            'type': 'string',
            'default': '',
            'description': 'Required for get_video_status',
        },
        {
            'displayName': 'Voice Id',
            'name': 'voice_id',
            'type': 'string',
            'default': '',
            'description': 'Optional: Specific voice ID',
        },
    ]
    inputs = {
        "action": {
            "type": "dropdown",
            "default": "generate_video",
            "options": ["generate_video", "get_video_status", "list_avatars", "list_voices"],
            "description": "Heygen action"
        },
        "avatar_id": {
            "type": "string",
            "default": "Daisy_public_2_20230913",
            "description": "The ID of the avatar to use"
        },
        "input_text": {
            "type": "string",
            "optional": True,
            "description": "Text for the avatar to speak"
        },
        "voice_id": {
            "type": "string",
            "optional": True,
            "description": "Optional: Specific voice ID"
        },
        "video_id": {
            "type": "string",
            "optional": True,
            "description": "Required for get_video_status"
        }
    }

    outputs = {
        "video_url": {"type": "string"},
        "video_id": {"type": "string"},
        "status": {"type": "string"},
        "result": {"type": "any"}
    }

    async def execute(self, input_data: Any, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        try:
            creds = await self.get_credential("heygen_auth")
            api_key = creds.get("api_key") or creds.get("token")
            
            if not api_key:
                return {"status": "error", "error": "Heygen API Key required"}

            headers = {
                "X-Api-Key": api_key,
                "Content-Type": "application/json"
            }
            
            action = self.get_config("action", "generate_video")
            base_url = "https://api.heygen.com/v2"

            async with aiohttp.ClientSession() as session:
                if action == "generate_video":
                    text = self.get_config("input_text") or str(input_data)
                    avatar_id = self.get_config("avatar_id")
                    voice_id = self.get_config("voice_id")
                    
                    payload = {
                        "video_inputs": [
                            {
                                "character": {
                                    "type": "avatar",
                                    "avatar_id": avatar_id
                                },
                                "input_text": text
                            }
                        ],
                        "test": False
                    }
                    
                    if voice_id:
                        payload["video_inputs"][0]["voice"] = {"type": "text", "voice_id": voice_id}
                    
                    url = f"{base_url}/video/generate"
                    async with session.post(url, headers=headers, json=payload) as resp:
                        res_data = await resp.json()
                        if resp.status >= 400:
                            return {"status": "error", "error": f"Heygen Error: {res_data.get('error', {}).get('message', 'Unknown Error')}"}
                        
                        video_id = res_data.get("data", {}).get("video_id")
                        return {
                            "status": "success", 
                            "data": {
                                "video_id": video_id,
                                "status": "processing",
                                "result": res_data
                            }
                        }

                elif action == "get_video_status":
                    video_id = self.get_config("video_id") or str(input_data)
                    if not video_id:
                        return {"status": "error", "error": "video_id required"}
                    
                    url = f"{base_url}/video/status?video_id={video_id}"
                    async with session.get(url, headers=headers) as resp:
                        res_data = await resp.json()
                        if resp.status >= 400:
                             return {"status": "error", "error": f"Heygen Error: {res_data.get('error', {}).get('message', 'Unknown Error')}"}
                        
                        status = res_data.get("data", {}).get("status")
                        video_url = res_data.get("data", {}).get("video_url")
                        
                        return {
                            "status": "success",
                            "data": {
                                "video_id": video_id,
                                "status": status,
                                "video_url": video_url,
                                "result": res_data
                            }
                        }

                elif action == "list_avatars":
                    url = f"{base_url}/avatars"
                    async with session.get(url, headers=headers) as resp:
                        res_data = await resp.json()
                        return {"status": "success", "data": {"result": res_data.get("data", {}).get("avatars", [])}}

            return {"status": "error", "error": f"Unsupported action: {action}"}

        except Exception as e:
            return {"status": "error", "error": f"Heygen Node Failed: {str(e)}"}