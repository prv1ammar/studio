from typing import Any, Dict, Optional
from ..base import BaseNode
from ..registry import register_node

@register_node("slack_message")
class SlackMessageNode(BaseNode):
    """
    Send messages to Slack channels using n8n-style configuration.
    Demonstrates the Resource/Operation pattern with dynamic visibility.
    """
    node_type = "slack_message"
    version = "1.0.0"
    category = "communication"
    icon = "Slack"
    color = "#4A154B"
    
    properties = [
        {
            "displayName": "Resource",
            "name": "resource",
            "type": "options",
            "options": [
                {"name": "Message", "value": "message"},
                {"name": "Channel", "value": "channel"},
                {"name": "User", "value": "user"},
            ],
            "default": "message",
            "description": "The resource to operate on"
        },
        {
            "displayName": "Operation",
            "name": "operation",
            "type": "options",
            "displayOptions": {
                "show": {
                    "resource": ["message"]
                }
            },
            "options": [
                {"name": "Send", "value": "send"},
                {"name": "Update", "value": "update"},
                {"name": "Delete", "value": "delete"},
            ],
            "default": "send",
            "description": "The operation to perform on messages"
        },
        {
            "displayName": "Operation",
            "name": "operation",
            "type": "options",
            "displayOptions": {
                "show": {
                    "resource": ["channel"]
                }
            },
            "options": [
                {"name": "List", "value": "list"},
                {"name": "Create", "value": "create"},
                {"name": "Archive", "value": "archive"},
            ],
            "default": "list",
            "description": "The operation to perform on channels"
        },
        {
            "displayName": "Operation",
            "name": "operation",
            "type": "options",
            "displayOptions": {
                "show": {
                    "resource": ["user"]
                }
            },
            "options": [
                {"name": "Get Info", "value": "info"},
                {"name": "Get Presence", "value": "presence"},
            ],
            "default": "info",
            "description": "The operation to perform on users"
        },
        {
            "displayName": "Channel",
            "name": "channel",
            "type": "string",
            "displayOptions": {
                "show": {
                    "resource": ["message"],
                    "operation": ["send"]
                }
            },
            "default": "",
            "placeholder": "#general",
            "required": True,
            "description": "The channel to send the message to"
        },
        {
            "displayName": "Message Text",
            "name": "text",
            "type": "string",
            "displayOptions": {
                "show": {
                    "resource": ["message"],
                    "operation": ["send", "update"]
                }
            },
            "default": "",
            "placeholder": "Hello from Tyboo Studio!",
            "required": True,
            "description": "The text of the message"
        },
        {
            "displayName": "Message Timestamp",
            "name": "ts",
            "type": "string",
            "displayOptions": {
                "show": {
                    "resource": ["message"],
                    "operation": ["update", "delete"]
                }
            },
            "default": "",
            "placeholder": "1234567890.123456",
            "required": True,
            "description": "The timestamp of the message to update or delete"
        },
        {
            "displayName": "Channel Name",
            "name": "channelName",
            "type": "string",
            "displayOptions": {
                "show": {
                    "resource": ["channel"],
                    "operation": ["create"]
                }
            },
            "default": "",
            "placeholder": "new-channel",
            "required": True,
            "description": "The name of the channel to create"
        },
        {
            "displayName": "Is Private",
            "name": "isPrivate",
            "type": "boolean",
            "displayOptions": {
                "show": {
                    "resource": ["channel"],
                    "operation": ["create"]
                }
            },
            "default": False,
            "description": "Whether the channel should be private"
        },
    ]

    credentials_required = ["slack_api"]

    async def execute(self, input_data: Any, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        resource = self.get_config("resource")
        operation = self.get_config("operation")
        
        # This is a demo - in production, you'd make actual Slack API calls
        return {
            "status": "success",
            "resource": resource,
            "operation": operation,
            "message": f"Would execute Slack {resource}:{operation}",
            "config": self.raw_config
        }
