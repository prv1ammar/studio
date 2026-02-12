from typing import Any, Dict, Optional
from ..base import BaseNode
from ..registry import register_node
import aiohttp
import json

@register_node("whatsapp_message_send")
class WhatsAppNode(BaseNode):
    """Sends messages via WhatsApp Business API (Meta)."""
    node_type = "whatsapp_message_send"
    version = "1.0.0"
    category = "communication"
    credentials_required = ["whatsapp_creds"]

    inputs = {
        "to": {"type": "string", "description": "Recipient phone number with country code"},
        "message": {"type": "string", "description": "Text message content"},
        "template_name": {"type": "string", "description": "Optional template name"}
    }
    outputs = {
        "id": {"type": "string", "description": "WhatsApp message ID"},
        "status": {"type": "string"}
    }

    async def execute(self, input_data: Any, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        try:
            creds = await self.get_credential("whatsapp_creds")
            token = creds.get("access_token")
            phone_number_id = creds.get("phone_number_id")
            
            if not token or not phone_number_id:
                return {"status": "error", "error": "WhatsApp Access Token and Phone Number ID are required.", "data": None}

            to_phone = input_data if isinstance(input_data, str) else self.get_config("to")
            message = self.get_config("message")
            template = self.get_config("template_name")

            if isinstance(input_data, dict):
                to_phone = input_data.get("to") or to_phone
                message = input_data.get("message") or message
                template = input_data.get("template") or template

            if not to_phone or (not message and not template):
                return {"status": "error", "error": "Recipient and Message/Template are required.", "data": None}

            # Normalize phone
            to_phone = to_phone.strip().replace(" ", "").replace("+", "")
            
            url = f"https://graph.facebook.com/v18.0/{phone_number_id}/messages"
            headers = {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "messaging_product": "whatsapp",
                "to": to_phone
            }
            
            if template:
                payload["type"] = "template"
                payload["template"] = {"name": template, "language": {"code": "en_US"}}
            else:
                payload["type"] = "text"
                payload["text"] = {"body": message}

            async with aiohttp.ClientSession() as session:
                async with session.post(url, headers=headers, json=payload) as resp:
                    result = await resp.json()
                    if resp.status >= 400:
                        return {"status": "error", "error": f"WhatsApp API Error: {result.get('error', {}).get('message')}", "data": result}
                    
                    return {
                        "status": "success",
                        "data": {
                            "id": result.get("messages", [{}])[0].get("id"),
                            "recipient": to_phone
                        }
                    }

        except Exception as e:
            return {"status": "error", "error": f"WhatsApp Node Failed: {str(e)}", "data": None}
