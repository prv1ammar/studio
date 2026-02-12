import json
from typing import Any, Dict, Optional, List
from pydantic import Field
from app.nodes.base import BaseNode, NodeConfig
from app.nodes.registry import register_node
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

class SlackConfig(NodeConfig):
    channel_id: str = Field(..., description="The ID or Name of the Slack channel")
    credentials_id: Optional[str] = Field(None, description="Slack Bot Token Credentials ID")

@register_node("slack_send_message")
class SlackSendMessageNode(BaseNode):
    async def execute(self, input_data: Any, context: Optional[Dict[str, Any]] = None) -> Any:
        channel = self.get_config("channel_id")
        
        creds_data = await self.get_credential("credentials_id")
        token = creds_data.get("token") or creds_data.get("bot_token") if creds_data else None
        
        if not token:
            return {"error": "Slack Bot Token is required."}

        client = WebClient(token=token)
        
        # Format text
        if isinstance(input_data, dict):
            text = f"🌐 *Studio Automation Update*\n```json\n{json.dumps(input_data, indent=2)}\n```"
        else:
            text = str(input_data)

        try:
            response = client.chat_postMessage(
                channel=channel,
                text=text
            )
            return {"status": "success", "ts": response["ts"], "channel": channel}
        except SlackApiError as e:
            return {"error": f"Slack API Error: {e.response['error']}"}

@register_node("slack_read_channel")
class SlackReadChannelNode(BaseNode):
    async def execute(self, input_data: Any, context: Optional[Dict[str, Any]] = None) -> Any:
        channel = self.get_config("channel_id")
        
        creds_data = await self.get_credential("credentials_id")
        token = creds_data.get("token") or creds_data.get("bot_token") if creds_data else None
        
        if not token:
            return {"error": "Slack Bot Token is required."}

        client = WebClient(token=token)
        
        try:
            response = client.conversations_history(channel=channel, limit=10)
            messages = [{"user": m.get("user"), "text": m.get("text"), "ts": m.get("ts")} for m in response["messages"]]
            return messages
        except SlackApiError as e:
            return {"error": f"Slack API Error: {e.response['error']}"}
