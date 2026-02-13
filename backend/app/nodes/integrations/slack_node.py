"""
Slack Integration Node - Studio Standard
Batch 40: Productivity Integrations
"""
from typing import Any, Dict, Optional, List
import json
from ...base import BaseNode
from ...registry import register_node

@register_node("slack_node")
class SlackNode(BaseNode):
    """
    Automate Slack actions (Send Message, Read Channel, Get Users).
    Uses AsyncWebClient for high-performance non-blocking operations.
    """
    node_type = "slack_node"
    version = "1.0.0"
    category = "productivity"
    credentials_required = ["slack_auth"]

    inputs = {
        "action": {
            "type": "dropdown",
            "default": "send_message",
            "options": ["send_message", "read_history", "list_users"],
            "description": "Action to perform"
        },
        "channel_id": {
            "type": "string",
            "description": "Channel ID or Name (e.g., #general, C12345)"
        },
        "message_text": {
            "type": "string",
            "optional": True,
            "description": "Message content (supports markdown)"
        },
        "limit": {
            "type": "number",
            "default": 10,
            "description": "Number of messages to retrieve"
        }
    }

    outputs = {
        "ts": {"type": "string"},
        "result": {"type": "json"},
        "messages": {"type": "array"}
    }

    async def execute(self, input_data: Any, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        try:
            # Check dependency
            try:
                from slack_sdk.web.async_client import AsyncWebClient
                from slack_sdk.errors import SlackApiError
            except ImportError:
                return {"status": "error", "error": "slack-sdk not installed. Run: pip install slack-sdk"}

            # Get Creds
            creds = await self.get_credential("slack_auth")
            token = None
            if creds:
                token = creds.get("token") or creds.get("bot_token")
            
            # Fallback
            if not token:
                token = self.get_config("bot_token")

            if not token:
                return {"status": "error", "error": "Slack Bot Token is required."}

            client = AsyncWebClient(token=token)
            action = self.get_config("action", "send_message")
            channel = self.get_config("channel_id")

            result_data = {}

            if action == "send_message":
                if not channel:
                     return {"status": "error", "error": "Channel ID is required to send message."}

                # Determine message content
                text = self.get_config("message_text")
                if input_data:
                    if isinstance(input_data, str):
                        text = input_data
                    elif isinstance(input_data, dict):
                        text = f"```json\n{json.dumps(input_data, indent=2)}\n```"
                    else:
                        text = str(input_data)
                
                if not text:
                    text = "Hello from Studio Agent!"

                response = await client.chat_postMessage(channel=channel, text=text)
                result_data = {
                    "ts": response["ts"],
                    "channel": response["channel"],
                    "message": response["message"]
                }

            elif action == "read_history":
                if not channel:
                     return {"status": "error", "error": "Channel ID is required to read history."}
                
                limit = int(self.get_config("limit", 10))
                response = await client.conversations_history(channel=channel, limit=limit)
                
                messages = []
                for m in response["messages"]:
                    messages.append({
                        "user": m.get("user"),
                        "text": m.get("text"),
                        "ts": m.get("ts"),
                        "type": m.get("type")
                    })
                
                result_data = {
                    "messages": messages,
                    "count": len(messages)
                }

            elif action == "list_users":
                response = await client.users_list()
                users = []
                for u in response["members"]:
                    if not u.get("deleted"):
                        users.append({
                            "id": u["id"],
                            "name": u["name"],
                            "real_name": u.get("real_name"),
                            "is_bot": u.get("is_bot")
                        })
                
                result_data = {
                    "users": users,
                    "count": len(users)
                }

            else:
                 return {"status": "error", "error": f"Unknown action: {action}"}

            return {
                "status": "success",
                "data": result_data
            }

        except SlackApiError as e:
            return {"status": "error", "error": f"Slack API Error: {e.response['error']}"}
        except Exception as e:
            return {"status": "error", "error": f"Slack execution failed: {str(e)}"}
