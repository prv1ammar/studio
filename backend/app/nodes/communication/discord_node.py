import json
import aiohttp
from typing import Any, Dict, Optional, List
from ..base import BaseNode
from ..registry import register_node

@register_node("discord_action")
class DiscordNode(BaseNode):
    """
    Automate Discord actions via Webhook or Bot Token.
    """
    node_type = "discord_action"
    version = "1.0.0"
    category = "communication"
    credentials_required = ["discord_auth"]

    inputs = {
        "webhook_url": {"type": "string", "optional": True},
        "channel_id": {"type": "string", "optional": True, "description": "Required for Bot Token mode"},
        "content": {"type": "string", "optional": True}
    }
    outputs = {
        "message_id": {"type": "string"},
        "status": {"type": "string"}
    }

    async def execute(self, input_data: Any, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        try:
            # 1. Resolve Auth
            creds = await self.get_credential("discord_auth")
            bot_token = creds.get("token") or creds.get("bot_token") if creds else self.get_config("bot_token")
            webhook_url = self.get_config("webhook_url")
            channel_id = self.get_config("channel_id")

            msg_content = str(input_data) if input_data else self.get_config("content", "New message from Studio")
            if isinstance(input_data, dict):
                 msg_content = f"```json\n{json.dumps(input_data, indent=2)}\n```"

            payload = {"content": msg_content}

            # Strategy A: Webhook (Simpler, no bot invite needed)
            if webhook_url:
                async with aiohttp.ClientSession() as session:
                    async with session.post(webhook_url, json=payload) as resp:
                        if resp.status >= 400:
                             return {"status": "error", "error": f"Discord Webhook Error: {await resp.text()}"}
                        return {"status": "success", "data": {"method": "webhook", "content": msg_content}}

            # Strategy B: Bot Token
            if bot_token and channel_id:
                api_url = f"https://discord.com/api/v10/channels/{channel_id}/messages"
                headers = {"Authorization": f"Bot {bot_token}", "Content-Type": "application/json"}
                async with aiohttp.ClientSession() as session:
                    async with session.post(api_url, headers=headers, json=payload) as resp:
                        result = await resp.json()
                        if resp.status >= 400:
                            return {"status": "error", "error": f"Discord API Error: {result.get('message')}"}
                        return {
                            "status": "success",
                            "data": {
                                "method": "bot",
                                "message_id": result.get("id"),
                                "content": msg_content
                            }
                        }

            return {"status": "error", "error": "Missing config: Provide Webhook URL or Bot Token + Channel ID."}

        except Exception as e:
            return {"status": "error", "error": f"Discord Node Error: {str(e)}"}
