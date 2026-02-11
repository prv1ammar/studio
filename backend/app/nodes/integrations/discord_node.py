import json
from typing import Any, Dict, Optional
import aiohttp
from pydantic import Field
from app.nodes.base import BaseNode, NodeConfig
from app.nodes.registry import register_node

class DiscordConfig(NodeConfig):
    webhook_url: Optional[str] = Field(None, description="Discord Webhook URL (for simple notifications)")
    bot_token: Optional[str] = Field(None, description="Discord Bot Token (for advanced interactions)")
    channel_id: Optional[str] = Field(None, description="Channel ID (if using Bot Token)")
    credentials_id: Optional[str] = Field(None, description="Credentials ID for Bot Token")

@register_node("discord_node")
class DiscordNode(BaseNode):
    node_id = "discord_node"
    config_model = DiscordConfig

    async def execute(self, input_data: Any, context: Optional[Dict[str, Any]] = None) -> Any:
        webhook_url = self.get_config("webhook_url")
        bot_token_creds = await self.get_credential("credentials_id")
        bot_token = bot_token_creds.get("token") if bot_token_creds else self.get_config("bot_token")
        channel_id = self.get_config("channel_id")

        payload = {
            "content": str(input_data)
        }
        
        # If input_data is a dictionary, format it as a code block
        if isinstance(input_data, dict):
            payload["content"] = f"```json\n{json.dumps(input_data, indent=2)}\n```"

        try:
            # 1. Prefer Webhook for simple notifications
            if webhook_url:
                async with aiohttp.ClientSession() as session:
                    async with session.post(webhook_url, json=payload) as resp:
                        if resp.status >= 400:
                            return {"error": f"Discord Webhook Error: {await resp.text()}"}
                        return {"status": "success", "method": "webhook"}

            # 2. Fallback to Bot Token for specific channels
            if bot_token and channel_id:
                api_url = f"https://discord.com/api/v10/channels/{channel_id}/messages"
                headers = {
                    "Authorization": f"Bot {bot_token}",
                    "Content-Type": "application/json"
                }
                async with aiohttp.ClientSession() as session:
                    async with session.post(api_url, headers=headers, json=payload) as resp:
                        result = await resp.json()
                        if resp.status >= 400:
                            return {"error": f"Discord API Error: {result.get('message')}"}
                        return {"status": "success", "method": "bot", "message_id": result.get("id")}

            return {"error": "Missing configuration: Either Webhook URL or Bot Token + Channel ID must be provided."}

        except Exception as e:
            return {"error": f"Discord Node Execution Failed: {str(e)}"}
