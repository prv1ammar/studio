from typing import Any, Dict, Optional, List
from pydantic import Field
from app.nodes.base import BaseNode, NodeConfig
from app.nodes.registry import register_node
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
import base64
from email.message import EmailMessage

class GmailConfig(NodeConfig):
    recipient: Optional[str] = Field(None, description="Default recipient email")
    subject: str = Field("Studio Automation Message", description="Email subject")
    credentials_id: Optional[str] = Field(None, description="Google OAuth Token Credentials ID")
    max_results: int = Field(5, description="Max messages to fetch")

@register_node("gmail_send_message")
class GmailSendMessageNode(BaseNode):
    node_id = "gmail_send_message"
    config_model = GmailConfig

    async def execute(self, input_data: Any, context: Optional[Dict[str, Any]] = None) -> Any:
        recipient = self.get_config("recipient")
        subject = self.get_config("subject")
        
        # Override from input_data if available
        if isinstance(input_data, dict):
            recipient = input_data.get("recipient", recipient)
            subject = input_data.get("subject", subject)
            message_text = input_data.get("message", str(input_data))
        else:
            message_text = str(input_data)

        creds_data = await self.get_credential("credentials_id")
        if not creds_data:
            return {"error": "Gmail OAuth credentials are required."}

        try:
            creds = Credentials.from_authorized_user_info(creds_data)
            service = build("gmail", "v1", credentials=creds)
            
            email_msg = EmailMessage()
            email_msg.set_content(message_text)
            email_msg['To'] = recipient
            email_msg['From'] = 'me'
            email_msg['Subject'] = subject
            
            encoded_message = base64.urlsafe_b64encode(email_msg.as_bytes()).decode()
            send_resp = service.users().messages().send(userId="me", body={'raw': encoded_message}).execute()
            
            return {"status": "success", "id": send_resp.get("id"), "recipient": recipient}
        except Exception as e:
            return {"error": f"Gmail Send Failed: {str(e)}"}

@register_node("gmail_fetch_messages")
class GmailFetchMessagesNode(BaseNode):
    node_id = "gmail_fetch_messages"
    config_model = GmailConfig

    async def execute(self, input_data: Any, context: Optional[Dict[str, Any]] = None) -> Any:
        max_results = self.get_config("max_results")
        creds_data = await self.get_credential("credentials_id")
        
        if not creds_data:
            return {"error": "Gmail OAuth credentials are required."}

        try:
            creds = Credentials.from_authorized_user_info(creds_data)
            service = build("gmail", "v1", credentials=creds)
            
            results = service.users().messages().list(userId="me", maxResults=max_results).execute()
            messages = results.get('messages', [])
            
            output = []
            for msg in messages:
                m = service.users().messages().get(userId='me', id=msg['id']).execute()
                snippet = m.get('snippet')
                headers = m.get('payload', {}).get('headers', [])
                subject = next((h['value'] for h in headers if h['name'] == 'Subject'), "No Subject")
                sender = next((h['value'] for h in headers if h['name'] == 'From'), "Unknown")
                
                output.append({
                    "id": msg['id'],
                    "sender": sender,
                    "subject": subject,
                    "snippet": snippet
                })
                
            return output
        except Exception as e:
            return {"error": f"Gmail Fetch Failed: {str(e)}"}
