"""
Cohere Chat Node - Studio Standard (Universal Method)
Batch 100: AI & LLM (The Grande Finale)
"""
from typing import Any, Dict, Optional, List
import aiohttp
import json
from ..base import BaseNode
from ..registry import register_node

@register_node("cohere_chat_node")
class CohereChatNode(BaseNode):
    """
    Generate chat completions using Cohere's Command models (RAG-ready).
    """
    node_type = "cohere_chat_node"
    version = "1.0.0"
    category = "ai"
    credentials_required = ["cohere_auth"]


    properties = [
        {
            'displayName': 'Chat History',
            'name': 'chat_history',
            'type': 'string',
            'default': '',
            'description': 'JSON array of history',
        },
        {
            'displayName': 'Max Tokens',
            'name': 'max_tokens',
            'type': 'string',
            'default': 1024,
            'description': 'Max tokens',
        },
        {
            'displayName': 'Message',
            'name': 'message',
            'type': 'string',
            'default': '',
            'description': 'User message',
            'required': True,
        },
        {
            'displayName': 'Model',
            'name': 'model',
            'type': 'options',
            'default': 'command-r-plus',
            'options': [
                {'name': 'Command-R-Plus', 'value': 'command-r-plus'},
                {'name': 'Command-R', 'value': 'command-r'},
                {'name': 'Command', 'value': 'command'},
            ],
            'description': 'Model to use',
        },
        {
            'displayName': 'Preamble',
            'name': 'preamble',
            'type': 'string',
            'default': '',
            'description': 'System prompt / Preamble',
        },
    ]
    inputs = {
        "model": {
            "type": "dropdown",
            "default": "command-r-plus",
            "options": ["command-r-plus", "command-r", "command"],
            "description": "Model to use"
        },
        "message": {
            "type": "string",
            "required": True,
            "description": "User message"
        },
        "preamble": {
            "type": "string",
            "optional": True,
            "description": "System prompt / Preamble"
        },
        "chat_history": {
            "type": "string",
            "optional": True,
            "description": "JSON array of history"
        },
        "max_tokens": {
            "type": "number",
            "default": 1024,
            "description": "Max tokens"
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
            creds = await self.get_credential("cohere_auth")
            api_key = creds.get("api_key")
            
            if not api_key:
                return {"status": "error", "error": "Cohere API Key required."}

            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
                "Accept": "application/json"
            }
            
            # 2. Prepare Payload
            model = self.get_config("model", "command-r-plus")
            message = self.get_config("message") or str(input_data)
            preamble = self.get_config("preamble")
            max_tokens = int(self.get_config("max_tokens", 1024))
            
            payload = {
                "model": model,
                "message": message,
                "max_tokens": max_tokens
            }
            if preamble:
                payload["preamble"] = preamble
                
            history_str = self.get_config("chat_history")
            if history_str:
                import json
                try:
                    history = json.loads(history_str) if isinstance(history_str, str) else history_str
                    payload["chat_history"] = history
                except:
                    pass
            
            # 3. Connect to Real API
            url = "https://api.cohere.com/v1/chat"
            
            async with aiohttp.ClientSession() as session:
                async with session.post(url, headers=headers, json=payload) as resp:
                    if resp.status != 200:
                        error_text = await resp.text()
                        return {"status": "error", "error": f"Cohere API Error: {resp.status} - {error_text}"}
                    
                    res_data = await resp.json()
                    
                    text = res_data.get("text", "")
                    
                    return {
                        "status": "success",
                        "data": {
                            "result": res_data,
                            "text": text
                        }
                    }

        except Exception as e:
            return {"status": "error", "error": f"Cohere Node Failed: {str(e)}"}