from typing import Any, Dict, Optional, List
from pydantic import Field
from app.nodes.base import BaseNode, NodeConfig
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

class SlackConfig(NodeConfig):
    channel_id: str = Field(..., description="The ID or Name of the Slack channel")
    credentials_id: Optional[str] = Field(None, description="Slack Bot Token Credentials ID")

class SlackSendMessageNode(BaseNode):
    node_id = "slack_send_message"
    config_model = SlackConfig

    async def execute(self, input_data: Any, context: Optional[Dict[str, Any]] = None) -> Any:
        channel = self.get_config("channel_id")
        creds_data = await self.get_credential("credentials_id")
        
        token = creds_data.get("token") if creds_data else None
        if not token:
            return {"error": "Slack Bot Token is required."}

        client = WebClient(token=token)
        
        # Prepare text - if input_data is a dict, convert to pretty string
        text = str(input_data)
        if isinstance(input_data, dict):
            text = f"```\n{json.dumps(input_data, indent=2)}\n```"

        try:
            response = client.chat_postMessage(
                channel=channel,
                text=text
            )
            return {"status": "success", "ts": response["ts"]}
        except SlackApiError as e:
            return {"error": f"Slack API Error: {e.response['error']}"}

class SlackReadChannelNode(BaseNode):
    node_id = "slack_read_channel"
    config_model = SlackConfig

    async def execute(self, input_data: Any, context: Optional[Dict[str, Any]] = None) -> Any:
        channel = self.get_config("channel_id")
        creds_data = await self.get_credential("credentials_id")
        
        token = creds_data.get("token") if creds_data else None
        if not token:
            return {"error": "Slack Bot Token is required."}

        client = WebClient(token=token)
        
        try:
            response = client.conversations_history(channel=channel, limit=10)
            messages = [{"user": m.get("user"), "text": m.get("text")} for m in response["messages"]]
            return messages
        except SlackApiError as e:
            return {"error": f"Slack API Error: {e.response['error']}"}

# Registration
from app.nodes.registry import register_node
import json
register_node("slack_send_message")(SlackSendMessageNode)
register_node("slack_read_channel")(SlackReadChannelNode)
