"""
OpenAI Whisper Audio Transcription Node - Studio Standard
Batch 42: Image & Audio
"""
from typing import Any, Dict, Optional
import os
import aiohttp
from ..base import BaseNode
from ..registry import register_node

@register_node("whisper_transcribe")
class WhisperTranscribeNode(BaseNode):
    """
    Transcribe audio files using OpenAI's Whisper model.
    Supports local files and URLs.
    """
    node_type = "whisper_transcribe"
    version = "1.0.0"
    category = "media"
    credentials_required = ["openai_auth"]


    properties = [
        {
            'displayName': 'File Path',
            'name': 'file_path',
            'type': 'string',
            'default': '',
            'description': 'Path to local audio file or URL',
        },
        {
            'displayName': 'Language',
            'name': 'language',
            'type': 'string',
            'default': '',
            'description': 'ISO-639-1 language code (e.g. 'en', 'fr')',
        },
        {
            'displayName': 'Model',
            'name': 'model',
            'type': 'options',
            'default': 'whisper-1',
            'options': [
                {'name': 'Whisper-1', 'value': 'whisper-1'},
            ],
            'description': 'Model version',
        },
        {
            'displayName': 'Response Format',
            'name': 'response_format',
            'type': 'options',
            'default': 'text',
            'options': [
                {'name': 'Json', 'value': 'json'},
                {'name': 'Text', 'value': 'text'},
                {'name': 'Srt', 'value': 'srt'},
                {'name': 'Verbose Json', 'value': 'verbose_json'},
                {'name': 'Vtt', 'value': 'vtt'},
            ],
            'description': 'Output format',
        },
        {
            'displayName': 'Temperature',
            'name': 'temperature',
            'type': 'string',
            'default': 0,
            'description': 'Sampling temperature (0-1)',
        },
    ]
    inputs = {
        "file_path": {
            "type": "string",
            "description": "Path to local audio file or URL"
        },
        "model": {
            "type": "dropdown",
            "default": "whisper-1",
            "options": ["whisper-1"],
            "description": "Model version"
        },
        "response_format": {
            "type": "dropdown",
            "default": "text",
            "options": ["json", "text", "srt", "verbose_json", "vtt"],
            "description": "Output format"
        },
        "temperature": {
            "type": "number",
            "default": 0,
            "description": "Sampling temperature (0-1)"
        },
        "language": {
            "type": "string",
            "optional": True,
            "description": "ISO-639-1 language code (e.g. 'en', 'fr')"
        }
    }

    outputs = {
        "text": {"type": "string"},
        "verbose_json": {"type": "json"}
    }

    async def execute(self, input_data: Any, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        temp_file_path = None
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
            
            # Get Input
            file_path = self.get_config("file_path")
            if isinstance(input_data, str) and input_data:
                file_path = input_data
            
            if not file_path:
                return {"status": "error", "error": "Audio file path or URL is required."}

            # Handle URL download
            if file_path.startswith("http"):
                try:
                    import tempfile
                    from urllib.parse import urlparse
                    
                    # Download to temp file
                    async with aiohttp.ClientSession() as session:
                        async with session.get(file_path) as resp:
                            if resp.status != 200:
                                return {"status": "error", "error": f"Failed to download audio: {resp.status}"}
                            
                            # Guess extension
                            parsed = urlparse(file_path)
                            ext = os.path.splitext(parsed.path)[1]
                            if not ext:
                                ext = ".mp3" # default

                            fd, temp_file_path = tempfile.mkstemp(suffix=ext)
                            os.write(fd, await resp.read())
                            os.close(fd)
                            file_path = temp_file_path
                except Exception as e:
                     return {"status": "error", "error": f"URL Download Failed: {str(e)}"}

            if not os.path.exists(file_path):
                 return {"status": "error", "error": f"File not found: {file_path}"}

            # Transcribe
            model = self.get_config("model", "whisper-1")
            response_format = self.get_config("response_format", "text")
            temperature = float(self.get_config("temperature", 0))
            language = self.get_config("language")

            with open(file_path, "rb") as audio_file:
                transcription = await client.audio.transcriptions.create(
                    model=model,
                    file=audio_file,
                    response_format=response_format,
                    temperature=temperature,
                    language=language
                )

            # Cleanup
            if temp_file_path and os.path.exists(temp_file_path):
                os.remove(temp_file_path)

            return {
                "status": "success",
                "data": {
                    "text": transcription if isinstance(transcription, str) else transcription.text,
                    "raw": transcription if not isinstance(transcription, str) else {"text": transcription}
                }
            }

        except Exception as e:
            # Cleanup
            if temp_file_path and os.path.exists(temp_file_path):
                try:
                    os.remove(temp_file_path)
                except:
                    pass
            return {"status": "error", "error": f"Whisper Transcription Failed: {str(e)}"}