from typing import Any, Dict, Optional
from ...base import BaseNode
import requests
import json

class NotificationNode(BaseNode):
    """
    Sends notifications via WhatsApp, Email, or SMS.
    Supports WhatsApp Business API, SMTP, and Twilio.
    """
    
    async def execute(self, input_data: Any, context: Optional[Dict[str, Any]] = None) -> Any:
        # Extract inputs
        recipient = None
        message = None
        if isinstance(input_data, dict):
            recipient = input_data.get("recipient")
            message = input_data.get("message") or input_data.get("input")
            channel = input_data.get("channel")
        elif isinstance(input_data, str):
            message = input_data
        
        # Fallback to config
        if not recipient:
            recipient = self.config.get("recipient") or "admin@tyboo.ma"
        if not message:
            message = self.config.get("message")
        if not channel:
            channel = self.config.get("channel") or "whatsapp"
        
        if not recipient or not message:
            print(f"⚠️ Notification Blocked: Missing recipient ({recipient}) or message ({message})")
            return {
                "status": "failed",
                "error": "Missing recipient or message"
            }
        
        # Route to appropriate channel
        result = None
        if channel.lower() == "whatsapp":
            result = await self._send_whatsapp(recipient, message)
        elif channel.lower() == "email":
            result = await self._send_email(recipient, message)
        elif channel.lower() == "sms":
            result = await self._send_sms(recipient, message)
        
        if not result:
            return f"Error: Unsupported or failed channel '{channel}'"
            
        if result.get("status") in ["sent", "sent (demo)"]:
            return f"✅ Notification successfully sent via {channel} to {recipient}."
        else:
            return f"❌ Notification failed via {channel}: {result.get('error', 'Unknown Error')}"
    
    async def _send_whatsapp(self, phone: str, message: str) -> Dict:
        """
        Send WhatsApp message via WhatsApp Business API.
        """
        # Get WhatsApp API credentials from config
        api_url = self.config.get("whatsapp_api_url", "https://graph.facebook.com/v18.0")
        phone_number_id = self.config.get("whatsapp_phone_number_id")
        access_token = self.config.get("whatsapp_access_token")
        
        if not phone_number_id or not access_token:
            print("\n" + "="*50)
            print("🚀 WHATSAPP DEMO MODE (NOT CONFIGURED)")
            print(f"TO:      {phone}")
            print(f"MESSAGE: {message}")
            print("="*50 + "\n")
            return {
                "status": "sent (demo)",
                "channel": "whatsapp",
                "recipient": phone,
                "note": "WhatsApp API not configured. Notification printed to console."
            }
        
        # Format phone number (remove spaces, ensure + prefix)
        phone = phone.strip().replace(" ", "")
        if not phone.startswith("+"):
            phone = f"+{phone}"
        
        # Build request
        url = f"{api_url}/{phone_number_id}/messages"
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "messaging_product": "whatsapp",
            "to": phone,
            "type": "text",
            "text": {
                "body": message
            }
        }
        
        try:
            response = requests.post(url, headers=headers, json=payload, timeout=10)
            
            if response.status_code == 200:
                return {
                    "status": "sent",
                    "channel": "whatsapp",
                    "recipient": phone,
                    "message_id": response.json().get("messages", [{}])[0].get("id")
                }
            else:
                return {
                    "status": "failed",
                    "channel": "whatsapp",
                    "error": f"API returned {response.status_code}: {response.text}"
                }
        except Exception as e:
            print(f"❌ Notification WhatsApp Channel Failure: {e}")
            return {
                "status": "failed",
                "channel": "whatsapp",
                "error": str(e)
            }
    
    async def _send_email(self, email: str, message: str) -> Dict:
        """
        Send email via SMTP.
        """
        import smtplib
        from email.mime.text import MIMEText
        from email.mime.multipart import MIMEMultipart
        
        # Get SMTP credentials from config
        smtp_host = self.config.get("smtp_host", "smtp.gmail.com")
        smtp_port = self.config.get("smtp_port", 587)
        smtp_user = self.config.get("smtp_user")
        smtp_password = self.config.get("smtp_password")
        from_email = self.config.get("from_email", smtp_user)
        subject = self.config.get("email_subject", "EasySpace Notification")
        
        if not smtp_user or not smtp_password:
            print("\n" + "="*50)
            print("🚀 NOTIFICATION DEMO MODE (SMTP NOT CONFIGURED)")
            print(f"TO:      {email}")
            print(f"FROM:    {from_email or 'system@tyboo.ma'}")
            print(f"SUBJECT: {subject}")
            print(f"MESSAGE: {message}")
            print("="*50 + "\n")
            
            return {
                "status": "sent (demo)",
                "channel": "email",
                "recipient": email,
                "note": "SMTP not configured. Notification printed to console."
            }
        
        try:
            # Create message
            msg = MIMEMultipart()
            msg['From'] = from_email
            msg['To'] = email
            msg['Subject'] = subject
            msg.attach(MIMEText(message, 'plain'))
            
            # Send email
            server = smtplib.SMTP(smtp_host, smtp_port)
            server.starttls()
            server.login(smtp_user, smtp_password)
            server.send_message(msg)
            server.quit()
            
            return {
                "status": "sent",
                "channel": "email",
                "recipient": email
            }
        except Exception as e:
            print(f"❌ Notification Email Channel Failure: {e}")
            return {
                "status": "failed",
                "channel": "email",
                "error": str(e)
            }
    
    async def _send_sms(self, phone: str, message: str) -> Dict:
        """
        Send SMS via Twilio.
        """
        # Get Twilio credentials from config
        account_sid = self.config.get("twilio_account_sid")
        auth_token = self.config.get("twilio_auth_token")
        from_phone = self.config.get("twilio_from_phone")
        
        if not account_sid or not auth_token or not from_phone:
            print("\n" + "="*50)
            print("🚀 SMS DEMO MODE (TWILIO NOT CONFIGURED)")
            print(f"TO:      {phone}")
            print(f"MESSAGE: {message}")
            print("="*50 + "\n")
            return {
                "status": "sent (demo)",
                "channel": "sms",
                "recipient": phone,
                "note": "Twilio API not configured. Notification printed to console."
            }
        
        try:
            # Twilio API endpoint
            url = f"https://api.twilio.com/2010-04-01/Accounts/{account_sid}/Messages.json"
            
            response = requests.post(
                url,
                auth=(account_sid, auth_token),
                data={
                    "From": from_phone,
                    "To": phone,
                    "Body": message
                },
                timeout=10
            )
            
            if response.status_code == 201:
                return {
                    "status": "sent",
                    "channel": "sms",
                    "recipient": phone,
                    "message_sid": response.json().get("sid")
                }
            else:
                return {
                    "status": "failed",
                    "channel": "sms",
                    "error": f"Twilio API returned {response.status_code}: {response.text}"
                }
        except Exception as e:
            print(f"❌ Notification SMS Channel Failure: {e}")
            return {
                "status": "failed",
                "channel": "sms",
                "error": str(e)
            }
    
    async def get_langchain_object(self, context: Optional[Dict[str, Any]] = None) -> Any:
        return None
