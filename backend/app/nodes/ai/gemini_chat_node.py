"""
Gemini Chat Node - Studio Standard (Universal Method)
Batch 100: AI & LLM (The Grande Finale)
"""
from typing import Any, Dict, Optional, List
import aiohttp
import json
from ..base import BaseNode
from ..registry import register_node

@register_node("gemini_chat_node")
class GeminiChatNode(BaseNode):
    """
    Generate chat completions using Google's Gemini models via Vertex AI or AI Studio.
    """
    node_type = "gemini_chat_node"
    version = "1.0.0"
    category = "ai"
    credentials_required = ["google_ai_auth"]


    properties = [
        {
            'displayName': 'Contents',
            'name': 'contents',
            'type': 'string',
            'default': '',
            'description': 'User prompt or JSON contents array',
            'required': True,
        },
        {
            'displayName': 'Model',
            'name': 'model',
            'type': 'options',
            'default': 'gemini-1.5-flash',
            'options': [
                {'name': 'Gemini-1.5-Flash', 'value': 'gemini-1.5-flash'},
                {'name': 'Gemini-1.5-Pro', 'value': 'gemini-1.5-pro'},
                {'name': 'Gemini-1.0-Pro', 'value': 'gemini-1.0-pro'},
            ],
            'description': 'Model to use',
        },
        {
            'displayName': 'System Instruction',
            'name': 'system_instruction',
            'type': 'string',
            'default': '',
            'description': 'System instruction',
        },
    ]
    inputs = {
        "model": {
            "type": "dropdown",
            "default": "gemini-1.5-flash",
            "options": ["gemini-1.5-flash", "gemini-1.5-pro", "gemini-1.0-pro"],
            "description": "Model to use"
        },
        "system_instruction": {
            "type": "string",
            "optional": True,
            "description": "System instruction"
        },
        "contents": {
            "type": "string",
            "required": True,
            "description": "User prompt or JSON contents array"
        }
    }

    outputs = {
        "result": {"type": "any"},
        "text": {"type": "string"},
        "status": {"type": "string"}
    }

    async def execute(self, input_data: Any, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        try:
            # 1. Authentication
            creds = await self.get_credential("google_ai_auth")
            api_key = creds.get("api_key")
            
            if not api_key:
                return {"status": "error", "error": "Google AI API Key required."}

            headers = {
                "Content-Type": "application/json"
            }
            
            # 2. Prepare Payload
            model = self.get_config("model", "gemini-1.5-flash")
            contents_input = self.get_config("contents") or str(input_data)
            
            import json
            contents_payload = []
            
            # Intelligent Parsing: String -> Single User Message, or JSON
            try:
                parsed = json.loads(contents_input)
                if isinstance(parsed, list):
                    contents_payload = parsed
                elif isinstance(parsed, dict):
                    contents_payload = [parsed]
                else:
                    contents_payload = [{"role": "user", "parts": [{"text": str(parsed)}]}]
            except:
                 # Treat as plain text user message
                 contents_payload = [{"role": "user", "parts": [{"text": contents_input}]}]

            payload = {
                "contents": contents_payload
            }
            
            system_instr = self.get_config("system_instruction")
            if system_instr:
                payload["system_instruction"] = {
                    "parts": [{"text": system_instr}]
                }
            
            # 3. Connect to Real API (AI Studio REST)
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
            
            async with aiohttp.ClientSession() as session:
                async with session.post(url, headers=headers, json=payload) as resp:
                    if resp.status != 200:
                        error_text = await resp.text()
                        return {"status": "error", "error": f"Gemini API Error: {resp.status} - {error_text}"}
                    
                    res_data = await resp.json()
                    
                    # Extract text
                    candidates = res_data.get("candidates", [])
                    text = ""
                    if candidates:
                        parts = candidates[0].get("content", {}).get("parts", [])
                        for p in parts:
                            text += p.get("text", "")
                    
                    return {
                        "status": "success",
                        "data": {
                            "result": res_data,
                            "text": text
                        }
                    }

        except Exception as e:
            return {"status": "error", "error": f"Gemini Node Failed: {str(e)}"}