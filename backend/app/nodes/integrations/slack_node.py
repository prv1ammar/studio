from typing import Any, Dict, Optional, List
import json
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
from ..base import BaseNode
from ..registry import register_node

@register_node("slack_action")
class SlackNode(BaseNode):
    """
    Automate Slack actions (Send Message, Read Channel).
    """
    node_type = "slack_action"
    version = "1.0.0"
    category = "communication"
    credentials_required = ["slack_auth"]

    inputs = {
        "action": {"type": "string", "default": "send_message", "enum": ["send_message", "read_channel"]},
        "channel_id": {"type": "string", "description": "Channel ID or Name"},
        "text": {"type": "string", "optional": True},
        "limit": {"type": "number", "default": 10}
    }
    outputs = {
        "ts": {"type": "string"},
        "messages": {"type": "array"},
        "status": {"type": "string"}
    }

    async def execute(self, input_data: Any, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        try:
            # 1. Resolve Auth
            creds = await self.get_credential("slack_auth")
            token = creds.get("token") or creds.get("bot_token") if creds else self.get_config("bot_token")
            
            if not token:
                return {"status": "error", "error": "Slack Bot Token is required."}

            client = WebClient(token=token)
            action = self.get_config("action", "send_message")
            channel = self.get_config("channel_id")

            if not channel:
                return {"status": "error", "error": "Channel ID is required."}

            if action == "send_message":
                text = str(input_data) if input_data else self.get_config("text", "Empty message from Studio")
                if isinstance(input_data, dict):
                    text = f"🌐 *Studio Automation Update*\n```json\n{json.dumps(input_data, indent=2)}\n```"
                
                response = client.chat_postMessage(channel=channel, text=text)
                return {
                    "status": "success",
                    "data": {
                        "ts": response["ts"],
                        "channel": channel,
                        "text": text
                    }
                }

            elif action == "read_channel":
                limit = int(self.get_config("limit", 10))
                response = client.conversations_history(channel=channel, limit=limit)
                messages = [{"user": m.get("user"), "text": m.get("text"), "ts": m.get("ts")} for m in response["messages"]]
                return {
                    "status": "success",
                    "data": {
                        "messages": messages,
                        "count": len(messages),
                        "channel": channel
                    }
                }

            return {"status": "error", "error": f"Unsupported action: {action}"}

        except SlackApiError as e:
            return {"status": "error", "error": f"Slack API Error: {e.response['error']}"}
        except Exception as e:
            return {"status": "error", "error": f"Slack Node Error: {str(e)}"}
