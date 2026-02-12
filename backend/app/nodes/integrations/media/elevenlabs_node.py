import aiohttp
from typing import Any, Dict, Optional
from ...base import BaseNode
from ...registry import register_node

@register_node("elevenlabs_tts")
class ElevenLabsNode(BaseNode):
    """Converts text to speech using ElevenLabs API."""
    node_type = "elevenlabs_tts"
    version = "1.0.0"
    category = "media"
    credentials_required = ["elevenlabs_auth"]

    inputs = {
        "text": {"type": "string", "description": "Text to convert to speech"},
        "voice_id": {"type": "string", "default": "21m00Tcm4TlvDq8ikWAM", "description": "ID of the voice to use"},
        "model_id": {"type": "string", "default": "eleven_monolingual_v1"}
    }
    outputs = {
        "audio_url": {"type": "string", "description": "URL to the generated audio (if hosted)"},
        "audio_base64": {"type": "string", "description": "Base64 encoded audio data"},
        "status": {"type": "string"}
    }

    async def execute(self, input_data: Any, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        creds = await self.get_credential("elevenlabs_auth")
        api_key = creds.get("api_key") if creds else self.get_config("api_key")

        if not api_key:
            return {"status": "error", "error": "ElevenLabs API Key is required.", "data": None}

        text = input_data if isinstance(input_data, str) else self.get_config("text")
        if isinstance(input_data, dict):
            text = input_data.get("text") or input_data.get("message") or text
        
        if not text:
            return {"status": "error", "error": "Text is required for TTS.", "data": None}

        voice_id = self.get_config("voice_id", "21m00Tcm4TlvDq8ikWAM")
        model_id = self.get_config("model_id", "eleven_monolingual_v1")
        
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
                "stability": 0.5,
                "similarity_boost": 0.5
            }
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=payload, headers=headers) as resp:
                    if resp.status >= 400:
                        err_text = await resp.text()
                        return {"status": "error", "error": f"ElevenLabs API Error: {err_text}", "data": None}
                    
                    audio_data = await resp.read()
                    import base64
                    audio_b64 = base64.b64encode(audio_data).decode('utf-8')
                    
                    return {
                        "status": "success",
                        "data": {
                            "audio_base64": audio_b64,
                            "format": "mp3",
                            "size_bytes": len(audio_data)
                        }
                    }
        except Exception as e:
            return {"status": "error", "error": f"ElevenLabs Node Failed: {str(e)}", "data": None}
