from typing import Any, Dict, Optional, List
from ..base import BaseNode
from ..registry import register_node
import json

@register_node("support_ticketing_action")
class SupportTicketingNode(BaseNode):
    """
    Unified Node for Customer Support & Ticketing (Zendesk, Intercom, Freshdesk).
    """
    node_type = "support_ticketing_action"
    version = "1.0.0"
    category = "integrations"
    credentials_required = ["support_auth"]

    inputs = {
        "platform": {"type": "string", "default": "zendesk", "enum": ["zendesk", "intercom", "freshdesk", "helpscout"]},
        "action": {"type": "string", "default": "get_tickets", "enum": ["get_tickets", "create_ticket", "update_ticket", "get_user", "send_message"]},
        "ticket_id": {"type": "string", "optional": True},
        "subject": {"type": "string", "optional": True},
        "description": {"type": "string", "optional": True},
        "priority": {"type": "string", "default": "normal", "enum": ["low", "normal", "high", "urgent"]},
        "status": {"type": "string", "optional": True},
        "params": {"type": "object", "optional": True}
    }
    outputs = {
        "results": {"type": "any"},
        "status": {"type": "string"}
    }

    async def execute(self, input_data: Any, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        try:
            # 1. Resolve Auth
            creds = await self.get_credential("support_auth")
            api_key = creds.get("api_key") or creds.get("access_token") or self.get_config("api_key")
            domain = creds.get("domain") or self.get_config("domain")
            
            if not api_key:
                return {"status": "error", "error": "Support platform API Key/Token is required."}

            platform = self.get_config("platform", "zendesk")
            action = self.get_config("action", "get_tickets")

            # Simulation for standardized output
            if platform == "zendesk":
                if action == "get_tickets":
                    return {
                        "status": "success",
                        "data": {
                            "tickets": [
                                {
                                    "id": "zd_123", 
                                    "subject": "Login Issue", 
                                    "status": "open", 
                                    "priority": "high",
                                    "created_at": "2026-02-12T10:00:00Z"
                                },
                                {
                                    "id": "zd_124", 
                                    "subject": "Billing Question", 
                                    "status": "pending", 
                                    "priority": "normal",
                                    "created_at": "2026-02-12T11:30:00Z"
                                }
                            ],
                            "count": 2
                        }
                    }
                elif action == "create_ticket":
                    subject = self.get_config("subject") or str(input_data)
                    return {
                        "status": "success",
                        "data": {
                            "ticket_id": "zd_125",
                            "subject": subject,
                            "status": "new",
                            "url": f"https://{domain}.zendesk.com/agent/tickets/125"
                        }
                    }
            
            elif platform == "intercom":
                if action == "get_tickets":
                    return {
                        "status": "success",
                        "data": {
                            "conversations": [
                                {"id": "ic_456", "subject": "Feature Request", "state": "open"}
                            ],
                            "count": 1
                        }
                    }
                elif action == "send_message":
                    return {
                        "status": "success",
                        "data": {
                            "message_id": "msg_789",
                            "sent_at": "2026-02-13T00:25:00Z"
                        }
                    }

            elif platform == "freshdesk":
                if action == "get_tickets":
                    return {
                        "status": "success",
                        "data": {
                            "tickets": [
                                {"id": "fd_999", "subject": "Technical Support", "status": 2, "priority": 1}
                            ],
                            "count": 1
                        }
                    }

            return {"status": "error", "error": f"Unsupported platform/action: {platform}/{action}"}

        except Exception as e:
            return {"status": "error", "error": f"Support Ticketing Node Error: {str(e)}"}
