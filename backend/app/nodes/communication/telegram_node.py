import aiohttp
import json
from typing import Any, Dict, Optional, List
from ..base import BaseNode
from ..registry import register_node

@register_node("telegram_action")
class TelegramNode(BaseNode):
    """
    Automate Telegram actions (Send Message).
    """
    node_type = "telegram_action"
    version = "1.0.0"
    category = "communication"
    credentials_required = ["telegram_auth"]

    inputs = {
        "chat_id": {"type": "string", "description": "Target Chat ID or @username"},
        "text": {"type": "string", "optional": True},
        "parse_mode": {"type": "string", "enum": ["Markdown", "HTML"], "default": "Markdown"}
    }
    outputs = {
        "message_id": {"type": "number"},
        "status": {"type": "string"}
    }

    async def execute(self, input_data: Any, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        try:
            # 1. Resolve Auth
            creds = await self.get_credential("telegram_auth")
            token = creds.get("token") or creds.get("bot_token") if creds else self.get_config("bot_token")
            chat_id = self.get_config("chat_id")

            if not token or not chat_id:
                return {"status": "error", "error": "Telegram Bot Token and Chat ID are required."}

            # 2. Prepare Payload
            message = str(input_data) if input_data is not None else self.get_config("text", "New update from Studio")
            if isinstance(input_data, dict):
                message = f" *Data Received*:\n```json\n{json.dumps(input_data, indent=2)}\n```"

            url = f"https://api.telegram.org/bot{token}/sendMessage"
            payload = {
                "chat_id": chat_id,
                "text": message,
                "parse_mode": self.get_config("parse_mode", "Markdown")
            }

            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=payload) as resp:
                    result = await resp.json()
                    if resp.status >= 400:
                        return {"status": "error", "error": f"Telegram Error: {result.get('description')}"}
                    
                    return {
                        "status": "success",
                        "data": {
                            "message_id": result.get("result", {}).get("message_id"),
                            "chat": result.get("result", {}).get("chat", {}).get("title") or chat_id
                        }
                    }

        except Exception as e:
            return {"status": "error", "error": f"Telegram Node Error: {str(e)}"}
