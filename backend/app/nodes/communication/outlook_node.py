"""
Microsoft Outlook Node - Studio Standard (Universal Method)
Batch 91: Productivity Suite (n8n Critical)
"""
from typing import Any, Dict, Optional, List
import aiohttp
from ...base import BaseNode
from ...registry import register_node

@register_node("outlook_node")
class OutlookNode(BaseNode):
    """
    Send emails and manage calendar via Microsoft Outlook (Graph API).
    """
    node_type = "outlook_node"
    version = "1.0.0"
    category = "communication"
    credentials_required = ["microsoft_auth"]

    inputs = {
        "action": {
            "type": "dropdown",
            "default": "send_email",
            "options": ["send_email", "list_messages", "get_message", "create_calendar_event"],
            "description": "Outlook action"
        },
        "to_email": {
            "type": "string",
            "optional": True
        },
        "subject": {
            "type": "string",
            "optional": True
        },
        "body": {
            "type": "string",
            "optional": True
        }
    }

    outputs = {
        "result": {"type": "any"},
        "status": {"type": "string"}
    }

    async def execute(self, input_data: Any, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        try:
            # 1. Authentication
            creds = await self.get_credential("microsoft_auth")
            access_token = creds.get("access_token")
            
            if not access_token:
                return {"status": "error", "error": "Microsoft Access Token required."}

            headers = {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json"
            }
            
            # 2. Connect to Real API (Microsoft Graph)
            base_url = "https://graph.microsoft.com/v1.0"
            action = self.get_config("action", "send_email")

            async with aiohttp.ClientSession() as session:
                if action == "send_email":
                    to_email = self.get_config("to_email")
                    subject = self.get_config("subject", "Studio Workflow Email")
                    body = self.get_config("body") or str(input_data)
                    
                    if not to_email:
                        return {"status": "error", "error": "to_email required"}
                    
                    url = f"{base_url}/me/sendMail"
                    payload = {
                        "message": {
                            "subject": subject,
                            "body": {
                                "contentType": "Text",
                                "content": body
                            },
                            "toRecipients": [{
                                "emailAddress": {"address": to_email}
                            }]
                        }
                    }
                    async with session.post(url, headers=headers, json=payload) as resp:
                        if resp.status not in [200, 202]:
                            return {"status": "error", "error": f"Outlook Error: {resp.status}"}
                        return {"status": "success", "data": {"result": {"message": "Email sent successfully"}}}

                elif action == "list_messages":
                    url = f"{base_url}/me/messages"
                    params = {"$top": 10}
                    async with session.get(url, headers=headers, params=params) as resp:
                        if resp.status != 200:
                            return {"status": "error", "error": f"Outlook Error: {resp.status}"}
                        res_data = await resp.json()
                        return {"status": "success", "data": {"result": res_data.get("value", [])}}

                elif action == "create_calendar_event":
                    subject = self.get_config("subject", "Studio Event")
                    from datetime import datetime, timedelta
                    start_time = (datetime.utcnow() + timedelta(hours=1)).isoformat() + "Z"
                    end_time = (datetime.utcnow() + timedelta(hours=2)).isoformat() + "Z"
                    
                    url = f"{base_url}/me/events"
                    payload = {
                        "subject": subject,
                        "start": {"dateTime": start_time, "timeZone": "UTC"},
                        "end": {"dateTime": end_time, "timeZone": "UTC"}
                    }
                    async with session.post(url, headers=headers, json=payload) as resp:
                        if resp.status not in [200, 201]:
                            return {"status": "error", "error": f"Outlook Error: {resp.status}"}
                        res_data = await resp.json()
                        return {"status": "success", "data": {"result": res_data}}

                return {"status": "error", "error": f"Unsupported action: {action}"}

        except Exception as e:
            return {"status": "error", "error": f"Outlook Node Failed: {str(e)}"}
