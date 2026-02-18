"""
WhatsApp Business Node (Meta) - Studio Standard
Batch 46: Communication & Marketing
"""
from typing import Any, Dict, Optional
import aiohttp
import json
from ..base import BaseNode
from ..registry import register_node

@register_node("whatsapp_meta")
class WhatsAppMetaNode(BaseNode):
    """
    Send messages via WhatsApp Business API (Meta).
    Supports: Direct Text, Business Templates.
    """
    node_type = "whatsapp_meta"
    version = "1.0.0"
    category = "communication"
    credentials_required = ["whatsapp_auth"]


    properties = [
        {
            'displayName': 'Language Code',
            'name': 'language_code',
            'type': 'string',
            'default': 'en_US',
            'description': 'Template language code',
        },
        {
            'displayName': 'Message',
            'name': 'message',
            'type': 'string',
            'default': '',
            'description': 'Message body for direct text',
        },
        {
            'displayName': 'Phone Number Id',
            'name': 'phone_number_id',
            'type': 'string',
            'default': '',
            'description': 'Meta Phone Number ID',
            'required': True,
        },
        {
            'displayName': 'Template Name',
            'name': 'template_name',
            'type': 'string',
            'default': '',
            'description': 'Meta Template Name',
        },
        {
            'displayName': 'To',
            'name': 'to',
            'type': 'string',
            'default': '',
            'description': 'Recipient phone number (with country code, no +)',
            'required': True,
        },
    ]
    inputs = {
        "phone_number_id": {
            "type": "string",
            "required": True,
            "description": "Meta Phone Number ID"
        },
        "to": {
            "type": "string",
            "required": True,
            "description": "Recipient phone number (with country code, no +)"
        },
        "message": {
            "type": "string",
            "description": "Message body for direct text"
        },
        "template_name": {
            "type": "string",
            "optional": True,
            "description": "Meta Template Name"
        },
        "language_code": {
            "type": "string",
            "default": "en_US",
            "description": "Template language code"
        }
    }

    outputs = {
        "message_id": {"type": "string"},
        "status": {"type": "string"},
        "recipient": {"type": "string"}
    }

    async def execute(self, input_data: Any, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        try:
            # 1. Resolve Auth
            creds = await self.get_credential("whatsapp_auth")
            token = None
            phone_id = self.get_config("phone_number_id")
            
            if creds:
                token = creds.get("access_token") or creds.get("token")
                phone_id = creds.get("phone_number_id") or phone_id
            
            if not token:
                token = self.get_config("access_token")

            if not token or not phone_id:
                return {"status": "error", "error": "WhatsApp/Meta Token and Phone Number ID are required."}

            to_phone = self.get_config("to")
            message = self.get_config("message")
            template = self.get_config("template_name")
            lang = self.get_config("language_code", "en_US")

            # Dynamic Overrides
            if isinstance(input_data, str):
                if "@" in input_data: # Filter out email if accidentally passed
                    pass
                else:
                    message = input_data
            elif isinstance(input_data, dict):
                to_phone = input_data.get("to") or to_phone
                message = input_data.get("message") or message
                template = input_data.get("template") or template

            if not to_phone:
                 return {"status": "error", "error": "Recipient (to) is required."}

            # Normalize phone (no +, no spaces)
            to_phone = str(to_phone).replace("+", "").replace(" ", "").replace("-", "")

            url = f"https://graph.facebook.com/v18.0/{phone_id}/messages"
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
                payload["template"] = {
                    "name": template,
                    "language": {"code": lang}
                }
            else:
                if not message:
                     return {"status": "error", "error": "Message body is required for direct text."}
                payload["type"] = "text"
                payload["text"] = {"body": message}

            async with aiohttp.ClientSession() as session:
                async with session.post(url, headers=headers, json=payload) as resp:
                    result = await resp.json()
                    
                    if resp.status >= 400:
                        return {
                            "status": "error", 
                            "error": f"WhatsApp API Error: {result.get('error', {}).get('message', 'Unknown Error')}",
                            "data": result
                        }
                    
                    messages = result.get("messages", [])
                    msg_id = messages[0].get("id") if messages else None
                    
                    return {
                        "status": "success",
                        "data": {
                            "message_id": msg_id,
                            "status": "sent",
                            "recipient": to_phone
                        }
                    }

        except Exception as e:
            return {"status": "error", "error": f"WhatsApp execution failed: {str(e)}"}