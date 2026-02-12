from typing import Any, Dict, Optional, List
from ...base import BaseNode
from ...registry import register_node
import aiohttp
import json

@register_node("assemblyai_action")
class AssemblyAINode(BaseNode):
    """Integrates with AssemblyAI for transcription and audio intelligence."""
    node_type = "assemblyai_action"
    version = "1.0.0"
    category = "media"
    credentials_required = ["assemblyai_auth"]

    inputs = {
        "action": {"type": "string", "enum": ["start_transcription", "get_transcript", "lemur_ai"], "default": "start_transcription"},
        "audio_url": {"type": "string", "description": "URL of the audio file to transcribe"},
        "transcript_id": {"type": "string", "description": "ID of an existing transcript"},
        "prompt": {"type": "string", "description": "Prompt for Lemur AI (only for lemur_ai action)"}
    }
    outputs = {
        "result": {"type": "object"},
        "status": {"type": "string"}
    }

    async def execute(self, input_data: Any, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        try:
            import assemblyai as aai
        except ImportError:
            return {"status": "error", "error": "assemblyai library not installed.", "data": None}

        creds = await self.get_credential("assemblyai_auth")
        api_key = creds.get("api_key") if creds else self.get_config("api_key")

        if not api_key:
            return {"status": "error", "error": "AssemblyAI API Key is required.", "data": None}

        aai.settings.api_key = api_key
        action = self.get_config("action", "start_transcription")

        try:
            if action == "start_transcription":
                audio_url = input_data if isinstance(input_data, str) and input_data.startswith("http") else self.get_config("audio_url")
                if isinstance(input_data, dict):
                    audio_url = input_data.get("audio_url") or audio_url
                
                if not audio_url:
                    return {"status": "error", "error": "Audio URL is required to start transcription.", "data": None}

                transcriber = aai.Transcriber()
                transcript = transcriber.submit(audio_url)
                return {
                    "status": "success",
                    "data": {
                        "transcript_id": transcript.id,
                        "status": transcript.status
                    }
                }

            elif action == "get_transcript":
                transcript_id = input_data if isinstance(input_data, str) and not input_data.startswith("http") else self.get_config("transcript_id")
                if isinstance(input_data, dict):
                    transcript_id = input_data.get("transcript_id") or transcript_id

                if not transcript_id:
                    return {"status": "error", "error": "Transcript ID is required.", "data": None}

                transcriber = aai.Transcriber()
                transcript = transcriber.get_by_id(transcript_id)
                
                return {
                    "status": "success",
                    "data": {
                        "id": transcript.id,
                        "status": transcript.status,
                        "text": transcript.text if transcript.status == "completed" else None,
                        "error": transcript.error if transcript.status == "error" else None,
                        "utterances": transcript.utterances if transcript.status == "completed" else None
                    }
                }

            elif action == "lemur_ai":
                transcript_id = self.get_config("transcript_id")
                prompt = self.get_config("prompt")
                
                if isinstance(input_data, dict):
                    transcript_id = input_data.get("transcript_id") or transcript_id
                    prompt = input_data.get("prompt") or prompt

                if not transcript_id or not prompt:
                    return {"status": "error", "error": "Transcript ID and Prompt are required for Lemur.", "data": None}

                transcript = aai.Transcript.get_by_id(transcript_id)
                if transcript.status != "completed":
                    return {"status": "error", "error": "Transcript must be 'completed' to use Lemur.", "data": None}

                result = transcript.lemur.task(prompt)
                return {
                    "status": "success",
                    "data": {
                        "response": result.response
                    }
                }

            return {"status": "error", "error": f"Unsupported AssemblyAI action: {action}", "data": None}

        except Exception as e:
            return {"status": "error", "error": f"AssemblyAI Node Failed: {str(e)}", "data": None}
