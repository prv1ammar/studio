import requests
import asyncio
from typing import Any, Dict, Optional, Type
from pydantic import BaseModel, Field
from langchain.tools import BaseTool
from backend.app.nodes.base import BaseNode

class TranscriptionInput(BaseModel):
    audio_url: str = Field(description="The URL of the audio file to transcribe.")

class TranscriptionTool(BaseTool):
    name: str = "transcription_tool"
    description: str = "Converts audio files from a URL into text using Whisper."
    args_schema: Type[BaseModel] = TranscriptionInput
    api_url: str = "https://toknroutertybot.tybotflow.com/v1/audio/transcriptions"
    api_key: str = "sk-siaV4eN9B0W-2X6PLMV4Vw"
    model: str = "gpt-4o-mini-transcribe"

    def _run(self, audio_url: str) -> str:
        try:
            response = requests.get(audio_url)
            if response.status_code != 200:
                return f"Error: Failed to download audio from {audio_url}"
            
            headers = {"Authorization": f"Bearer {self.api_key}"}
            files = {"file": ("audio.ogg", response.content, "application/octet-stream")}
            data = {"model": self.model}
            
            res = requests.post(self.api_url, headers=headers, files=files, data=data)
            if res.status_code == 200:
                return res.json().get("text", "")
            return f"Error: Transcription failed with status {res.status_code}"
        except Exception as e:
            return f"Error: {str(e)}"

class TranscriptionNode(BaseNode):
    """
    Node for converting audio to text using a specialized Whisper endpoint, wrapped as a LangChain tool.
    """
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self.tool = TranscriptionTool(
            api_url=self.config.get("api_url", "https://toknroutertybot.tybotflow.com/v1/audio/transcriptions"),
            api_key=self.config.get("api_key", "sk-siaV4eN9B0W-2X6PLMV4Vw"),
            model=self.config.get("model", "gpt-4o-mini-transcribe")
        )

    async def execute(self, input_data: Any, context: Optional[Dict[str, Any]] = None) -> Any:
        # Determine audio_url from input
        audio_url = None
        if isinstance(input_data, str):
            audio_url = input_data
        elif isinstance(input_data, dict):
            audio_url = input_data.get("audio_url") or input_data.get("message") or input_data.get("input")
            
        # Check if it looks like an audio URL
        is_audio = audio_url and isinstance(audio_url, str) and (
            audio_url.endswith(".mp3") or 
            audio_url.endswith(".ogg") or 
            audio_url.endswith(".wav") or 
            audio_url.endswith(".m4a") or
            "audio" in audio_url
        )

        # If it's valid audio, transcribe it
        if is_audio:
            result = await asyncio.to_thread(self.tool._run, audio_url)
            if result.startswith("Error"):
                return {"error": result, "status": "failed", "text": result} # Pass error as text too
            return result # Return raw text so next node gets a string
        
        # If NOT audio (e.g. text message), just pass it through!
        # This allows the node to sit in the middle of the flow safely
        if isinstance(input_data, str):
            return input_data
        if isinstance(input_data, dict):
             # Try to return the most meaningful text field
            return input_data.get("message") or input_data.get("text") or input_data.get("input") or str(input_data)
        
        return str(input_data)

    async def get_langchain_object(self, context: Optional[Dict[str, Any]] = None) -> Any:
        return self.tool
