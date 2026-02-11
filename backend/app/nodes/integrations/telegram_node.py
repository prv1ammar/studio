import aiohttp
import json
from typing import Any, Dict, Optional
from pydantic import Field
from app.nodes.base import BaseNode, NodeConfig
from app.nodes.registry import register_node

class TelegramConfig(NodeConfig):
    bot_token: Optional[str] = Field(None, description="Telegram Bot Token")
    chat_id: Optional[str] = Field(None, description="Target Chat ID or @username")
    credentials_id: Optional[str] = Field(None, description="Telegram Credentials ID")

@register_node("telegram_node")
class TelegramNode(BaseNode):
    node_id = "telegram_node"
    config_model = TelegramConfig

    async def execute(self, input_data: Any, context: Optional[Dict[str, Any]] = None) -> Any:
        # 1. Auth Retrieval
        creds = await self.get_credential("credentials_id")
        token = creds.get("token") if creds else self.get_config("bot_token")
        chat_id = self.get_config("chat_id")

        if not token or not chat_id:
            return {"error": "Telegram Bot Token and Chat ID are required."}

        # 2. Payload Preparation
        message = str(input_data)
        if isinstance(input_data, dict):
            message = f"📦 *Data Received*:\n```json\n{json.dumps(input_data, indent=2)}\n```"

        url = f"https://api.telegram.org/bot{token}/sendMessage"
        payload = {
            "chat_id": chat_id,
            "text": message,
            "parse_mode": "Markdown"
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=payload) as resp:
                    result = await resp.json()
                    if resp.status >= 400:
                        return {"error": f"Telegram API Error: {result.get('description')}"}
                    return {"status": "success", "message_id": result.get("result", {}).get("message_id")}
        except Exception as e:
            return {"error": f"Telegram Node Failed: {str(e)}"}
