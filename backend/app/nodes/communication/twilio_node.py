from typing import Any, Dict, Optional
from ..base import BaseNode
from ..registry import register_node
import aiohttp

@register_node("twilio_sms_send")
class TwilioSMSNode(BaseNode):
    """Sends SMS messages via Twilio API."""
    node_type = "twilio_sms_send"
    version = "1.0.0"
    category = "communication"
    credentials_required = ["twilio_creds"]

    inputs = {
        "to": {"type": "string", "description": "Recipient phone number (e.g. +1234567890)"},
        "from": {"type": "string", "description": "Your Twilio phone number"},
        "body": {"type": "string", "description": "Message content"}
    }
    outputs = {
        "sid": {"type": "string", "description": "Twilio Message SID"},
        "status": {"type": "string"}
    }

    async def execute(self, input_data: Any, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        try:
            creds = await self.get_credential("twilio_creds")
            account_sid = creds.get("account_sid")
            auth_token = creds.get("auth_token")
            
            if not account_sid or not auth_token:
                return {"status": "error", "error": "Twilio Account SID and Auth Token are required.", "data": None}

            to_phone = input_data if isinstance(input_data, str) else self.get_config("to")
            from_phone = self.get_config("from") or creds.get("from_phone")
            body = self.get_config("body")
            
            if isinstance(input_data, dict):
                to_phone = input_data.get("to") or to_phone
                body = input_data.get("body") or input_data.get("message") or body

            if not to_phone or not body or not from_phone:
                return {"status": "error", "error": "Recipient, Message, and From Phone are required.", "data": None}

            url = f"https://api.twilio.com/2010-04-01/Accounts/{account_sid}/Messages.json"
            
            async with aiohttp.ClientSession() as session:
                auth = aiohttp.BasicAuth(account_sid, auth_token)
                data = {
                    "To": to_phone,
                    "From": from_phone,
                    "Body": body
                }
                async with session.post(url, auth=auth, data=data) as resp:
                    result = await resp.json()
                    if resp.status >= 400:
                        return {"status": "error", "error": f"Twilio API Error: {result.get('message')}", "data": result}
                    
                    return {
                        "status": "success",
                        "data": {
                            "sid": result.get("sid"),
                            "to": to_phone,
                            "status": result.get("status")
                        }
                    }

        except Exception as e:
            return {"status": "error", "error": f"Twilio Node Failed: {str(e)}", "data": None}
