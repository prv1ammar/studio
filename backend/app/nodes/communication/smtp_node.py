from typing import Any, Dict, Optional
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from ..base import BaseNode
from ..registry import register_node

@register_node("email_smtp_send")
class SmtpEmailNode(BaseNode):
    """Sends emails via generic SMTP (Gmail, SendGrid, Outlook, etc.)."""
    node_type = "email_smtp_send"
    version = "1.0.0"
    category = "communication"
    credentials_required = ["smtp_creds"]

    inputs = {
        "to": {"type": "string", "description": "Recipient email address"},
        "subject": {"type": "string", "description": "Email subject line"},
        "body": {"type": "string", "description": "Email body content"},
        "html": {"type": "boolean", "default": False}
    }
    outputs = {
        "recipient": {"type": "string"},
        "status": {"type": "string"}
    }

    async def execute(self, input_data: Any, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        try:
            creds = await self.get_credential("smtp_creds")
            host = creds.get("host")
            port = int(creds.get("port", 587))
            user = creds.get("user")
            password = creds.get("password")
            from_email = creds.get("from_email") or user

            if not host or not user or not password:
                return {"status": "error", "error": "SMTP Host, User, and Password are required.", "data": None}

            recipient = input_data if isinstance(input_data, str) and "@" in input_data else self.get_config("to")
            subject = self.get_config("subject", "Automation Studio Message")
            body = self.get_config("body", "")
            is_html = self.get_config("html", False)

            if isinstance(input_data, dict):
                recipient = input_data.get("to") or recipient
                subject = input_data.get("subject") or subject
                body = input_data.get("body") or input_data.get("message") or body

            if not recipient or not body:
                return {"status": "error", "error": "Recipient and Body are required.", "data": None}

            # Create message
            msg = MIMEMultipart()
            msg['From'] = from_email
            msg['To'] = recipient
            msg['Subject'] = subject
            msg.attach(MIMEText(body, 'html' if is_html else 'plain'))
            
            # Send email (synchronous but wrapped in executor by engine if needed)
            # For now, standard smtplib
            server = smtplib.SMTP(host, port)
            server.starttls()
            server.login(user, password)
            server.send_message(msg)
            server.quit()
            
            return {
                "status": "success",
                "data": {
                    "recipient": recipient,
                    "subject": subject
                }
            }

        except Exception as e:
            return {"status": "error", "error": f"SMTP Node Failed: {str(e)}", "data": None}
