"""
Twilio Communication Node - Studio Standard
Batch 46: Communication & Marketing
"""
from typing import Any, Dict, Optional
import aiohttp
from ..base import BaseNode
from ..registry import register_node

@register_node("twilio_node")
class TwilioNode(BaseNode):
    """
    Send SMS and WhatsApp messages using Twilio.
    Supports: SMS, WhatsApp.
    """
    node_type = "twilio_node"
    version = "1.0.0"
    category = "communication"
    credentials_required = ["twilio_auth"]


    properties = [
        {
            'displayName': 'Channel',
            'name': 'channel',
            'type': 'options',
            'default': 'sms',
            'options': [
                {'name': 'Sms', 'value': 'sms'},
                {'name': 'Whatsapp', 'value': 'whatsapp'},
            ],
            'description': 'Communication channel',
        },
        {
            'displayName': 'From Number',
            'name': 'from_number',
            'type': 'string',
            'default': '',
            'description': 'Twilio sender number (or 'whatsapp:+1234567890')',
        },
        {
            'displayName': 'Media Url',
            'name': 'media_url',
            'type': 'string',
            'default': '',
            'description': 'Optional media URL for MMS',
        },
        {
            'displayName': 'Message',
            'name': 'message',
            'type': 'string',
            'default': '',
            'description': 'Message content',
            'required': True,
        },
        {
            'displayName': 'To',
            'name': 'to',
            'type': 'string',
            'default': '',
            'description': 'Recipient phone number (e.g., '+1234567890')',
            'required': True,
        },
    ]
    inputs = {
        "channel": {
            "type": "dropdown",
            "default": "sms",
            "options": ["sms", "whatsapp"],
            "description": "Communication channel"
        },
        "to": {
            "type": "string",
            "required": True,
            "description": "Recipient phone number (e.g., '+1234567890')"
        },
        "from_number": {
            "type": "string",
            "description": "Twilio sender number (or 'whatsapp:+1234567890')"
        },
        "message": {
            "type": "string",
            "required": True,
            "description": "Message content"
        },
        "media_url": {
            "type": "string",
            "optional": True,
            "description": "Optional media URL for MMS"
        }
    }

    outputs = {
        "sid": {"type": "string"},
        "status": {"type": "string"},
        "uri": {"type": "string"}
    }

    async def execute(self, input_data: Any, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        try:
            # 1. Resolve Auth
            creds = await self.get_credential("twilio_auth")
            account_sid = None
            auth_token = None
            
            if creds:
                account_sid = creds.get("account_sid")
                auth_token = creds.get("auth_token") or creds.get("token")
            
            if not account_sid or not auth_token:
                account_sid = self.get_config("account_sid")
                auth_token = self.get_config("auth_token")

            if not account_sid or not auth_token:
                return {"status": "error", "error": "Twilio Account SID and Auth Token are required."}

            channel = self.get_config("channel", "sms")
            to_phone = self.get_config("to")
            from_phone = self.get_config("from_number")
            message_body = self.get_config("message")
            media_url = self.get_config("media_url")

            # Dynamic Overrides
            if isinstance(input_data, str):
                message_body = input_data
            elif isinstance(input_data, dict):
                to_phone = input_data.get("to") or to_phone
                message_body = input_data.get("message") or input_data.get("body") or message_body
                from_phone = input_data.get("from") or from_phone

            if not to_phone or not message_body:
                 return {"status": "error", "error": "Recipient (to) and Message content are required."}

            # Prepare WhatsApp prefixing
            if channel == "whatsapp":
                if not to_phone.startswith("whatsapp:"):
                    to_phone = f"whatsapp:{to_phone}"
                if from_phone and not from_phone.startswith("whatsapp:"):
                    from_phone = f"whatsapp:{from_phone}"

            url = f"https://api.twilio.com/2010-04-01/Accounts/{account_sid}/Messages.json"
            
            async with aiohttp.ClientSession() as session:
                auth = aiohttp.BasicAuth(account_sid, auth_token)
                data = {
                    "To": to_phone,
                    "Body": message_body
                }
                if from_phone:
                    data["From"] = from_phone
                if media_url:
                    data["MediaUrl"] = media_url

                async with session.post(url, auth=auth, data=data) as resp:
                    result = await resp.json()
                    
                    if resp.status >= 400:
                        return {
                            "status": "error", 
                            "error": f"Twilio API Error: {result.get('message', 'Unknown Error')}",
                            "data": result
                        }
                    
                    return {
                        "status": "success",
                        "data": {
                            "sid": result.get("sid"),
                            "status": result.get("status"),
                            "uri": result.get("uri"),
                            "to": to_phone
                        }
                    }

        except Exception as e:
            return {"status": "error", "error": f"Twilio execution failed: {str(e)}"}