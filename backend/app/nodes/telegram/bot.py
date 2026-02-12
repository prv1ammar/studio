from typing import Any, Dict, Optional
from pydantic import Field
from app.nodes.base import BaseNode, NodeConfig
from app.nodes.registry import register_node
import aiohttp
import json

class TelegramConfig(NodeConfig):
    chat_id: str = Field(..., description="Target Chat ID or @channelusername")
    credentials_id: Optional[str] = Field(None, description="Telegram Bot Token Credentials ID")

@register_node("telegram_bot_send")
class TelegramBotNode(BaseNode):
    async def execute(self, input_data: Any, context: Optional[Dict[str, Any]] = None) -> Any:
        chat_id = self.get_config("chat_id")
        
        creds_data = await self.get_credential("credentials_id")
        bot_token = creds_data.get("token") or creds_data.get("bot_token") if creds_data else None
        
        if not bot_token:
            return {"error": "Telegram Bot Token is required."}
            
        # Parse message
        message_text = ""
        if isinstance(input_data, dict):
            message_text = input_data.get("text") or input_data.get("message")
            if not message_text:
                message_text = f"```json\n{json.dumps(input_data, indent=2)}\n```"
        else:
            message_text = str(input_data)
        
        url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        payload = {
            "chat_id": chat_id,
            "text": message_text,
            "parse_mode": "Markdown"
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload) as response:
                result = await response.json()
                if not result.get("ok"):
                    # Fallback to plain text if Markdown fails
                    if "can't parse" in result.get("description", "").lower():
                        payload["parse_mode"] = ""
                        async with session.post(url, json=payload) as retry_resp:
                            result = await retry_resp.json()
                    
                    if not result.get("ok"):
                        return {"error": result.get("description", "Unknown Telegram Error")}
                
                return result.get("result", {})
