import json
from typing import Any, Dict, Optional
from pydantic import Field
from app.nodes.base import BaseNode, NodeConfig
from app.nodes.registry import register_node
import aiohttp

class DiscordConfig(NodeConfig):
    bot_name: str = Field("Studio Automation", description="Bot display name")
    credentials_id: Optional[str] = Field(None, description="Discord Webhook URL Credentials ID")
    webhook_url: Optional[str] = Field(None, description="Direct Webhook URL (Fallback)")

@register_node("discord_webhook")
class DiscordWebhookNode(BaseNode):
    async def execute(self, input_data: Any, context: Optional[Dict[str, Any]] = None) -> Any:
        bot_name = self.get_config("bot_name", "Studio Automation")
        
        creds_data = await self.get_credential("credentials_id")
        webhook_url = creds_data.get("url") or creds_data.get("webhook_url") if creds_data else self.get_config("webhook_url")
        
        if not webhook_url:
            return {"error": "Discord Webhook URL is required (via Credentials or Config)."}
            
        payload = {
            "username": bot_name
        }

        # Handle complex objects (embeds) or plain text
        if isinstance(input_data, dict):
            if "embeds" in input_data:
                payload["embeds"] = input_data["embeds"]
                payload["content"] = input_data.get("content", "")
            else:
                payload["content"] = f"```json\n{json.dumps(input_data, indent=2)}\n```"
        else:
            payload["content"] = str(input_data)

        async with aiohttp.ClientSession() as session:
            async with session.post(webhook_url, json=payload) as response:
                if response.status >= 400:
                    text = await response.text()
                    return {"error": f"Discord Error {response.status}", "details": text}
                
                return {"status": "success", "message": "Discord notification dispatched"}
