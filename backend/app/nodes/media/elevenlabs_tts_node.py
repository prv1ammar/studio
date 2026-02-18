"""
ElevenLabs Text-to-Speech Node - Studio Standard
Batch 42: Image & Audio
"""
from typing import Any, Dict, Optional
import aiohttp
import base64
from ..base import BaseNode
from ..registry import register_node

@register_node("elevenlabs_tts")
class ElevenLabsNode(BaseNode):
    """
    Convert text to lifelike speech using ElevenLabs API.
    Supports Multilingual v2 and Monolingual v1 models.
    """
    node_type = "elevenlabs_tts"
    version = "1.0.0"
    category = "media"
    credentials_required = ["elevenlabs_auth"]


    properties = [
        {
            'displayName': 'Model Id',
            'name': 'model_id',
            'type': 'options',
            'default': 'eleven_monolingual_v1',
            'options': [
                {'name': 'Eleven Monolingual V1', 'value': 'eleven_monolingual_v1'},
                {'name': 'Eleven Multilingual V2', 'value': 'eleven_multilingual_v2'},
            ],
            'description': 'Speech synthesis model',
        },
        {
            'displayName': 'Similarity Boost',
            'name': 'similarity_boost',
            'type': 'string',
            'default': 0.75,
            'description': 'Clarity + Similarity boost (0-1)',
        },
        {
            'displayName': 'Stability',
            'name': 'stability',
            'type': 'string',
            'default': 0.5,
            'description': 'Voice stability (0-1)',
        },
        {
            'displayName': 'Text',
            'name': 'text',
            'type': 'string',
            'default': '',
            'description': 'Text to speak',
            'required': True,
        },
        {
            'displayName': 'Voice Id',
            'name': 'voice_id',
            'type': 'string',
            'default': '21m00Tcm4TlvDq8ikWAM',
            'description': 'Voice ID (e.g., specific character)',
        },
    ]
    inputs = {
        "text": {
            "type": "string",
            "required": True,
            "description": "Text to speak"
        },
        "voice_id": {
            "type": "string",
            "default": "21m00Tcm4TlvDq8ikWAM", # Rachel
            "description": "Voice ID (e.g., specific character)"
        },
        "model_id": {
            "type": "dropdown",
            "default": "eleven_monolingual_v1",
            "options": ["eleven_monolingual_v1", "eleven_multilingual_v2"],
            "description": "Speech synthesis model"
        },
        "stability": {
            "type": "number",
            "default": 0.5,
            "description": "Voice stability (0-1)"
        },
        "similarity_boost": {
            "type": "number",
            "default": 0.75,
            "description": "Clarity + Similarity boost (0-1)"
        }
    }

    outputs = {
        "audio_base64": {"type": "string"},
        "audio_url": {"type": "string"}, # Placeholder if stored
        "format": {"type": "string"}
    }

    async def execute(self, input_data: Any, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        try:
            # Get Creds
            creds = await self.get_credential("elevenlabs_auth")
            api_key = creds.get("api_key") if creds else self.get_config("api_key")
            
            if not api_key:
                return {"status": "error", "error": "ElevenLabs API Key is required."}

            # Get Inputs
            text = self.get_config("text")
            if isinstance(input_data, str) and input_data:
                text = input_data
            elif isinstance(input_data, dict):
                text = input_data.get("text") or input_data.get("message") or text
            
            if not text:
                return {"status": "error", "error": "Text input is required."}

            voice_id = self.get_config("voice_id", "21m00Tcm4TlvDq8ikWAM")
            model_id = self.get_config("model_id", "eleven_monolingual_v1")
            stability = float(self.get_config("stability", 0.5))
            similarity = float(self.get_config("similarity_boost", 0.75))

            url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
            headers = {
                "Accept": "audio/mpeg",
                "Content-Type": "application/json",
                "xi-api-key": api_key
            }
            payload = {
                "text": text,
                "model_id": model_id,
                "voice_settings": {
                    "stability": stability,
                    "similarity_boost": similarity
                }
            }

            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=payload, headers=headers) as resp:
                    if resp.status >= 400:
                         err_text = await resp.text()
                         return {"status": "error", "error": f"ElevenLabs API Error: {err_text}"}
                    
                    audio_data = await resp.read()
                    
                    # Convert to Base64 for frontend
                    audio_b64 = base64.b64encode(audio_data).decode('utf-8')
                    
                    return {
                        "status": "success",
                        "data": {
                            "audio_base64": audio_b64,
                            "format": "mp3",
                            "size_bytes": len(audio_data),
                            "voice_id": voice_id
                        }
                    }

        except Exception as e:
            return {"status": "error", "error": f"ElevenLabs TTS Failed: {str(e)}"}