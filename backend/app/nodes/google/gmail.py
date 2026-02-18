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

@register_node("gmail_send")
class GmailSendMessageNode(BaseNode):
    """Sends an email via Gmail API."""
    node_type = "gmail_send"
    version = "1.0.0"
    category = "communication"
    credentials_required = ["google_oauth"]


    properties = [
        {
            'displayName': 'Body',
            'name': 'body',
            'type': 'string',
            'default': '',
            'description': 'Email content body',
        },
        {
            'displayName': 'Recipient',
            'name': 'recipient',
            'type': 'string',
            'default': '',
            'description': 'Recipient email address',
        },
        {
            'displayName': 'Subject',
            'name': 'subject',
            'type': 'string',
            'default': '',
            'description': 'Email subject line',
        },
    ]
    inputs = {
        "recipient": {"type": "string", "description": "Recipient email address"},
        "subject": {"type": "string", "description": "Email subject line"},
        "body": {"type": "string", "description": "Email content body"}
    }
    outputs = {
        "id": {"type": "string", "description": "Sent message ID"},
        "recipient": {"type": "string"},
        "status": {"type": "string"}
    }

    async def execute(self, input_data: Any, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        recipient = self.get_config("recipient")
        subject = self.get_config("subject")
        
        # Override from input_data if available
        if isinstance(input_data, dict):
            recipient = input_data.get("recipient") or input_data.get("to") or recipient
            subject = input_data.get("subject") or subject
            message_text = input_data.get("body") or input_data.get("message") or str(input_data)
        else:
            message_text = str(input_data) if input_data else self.get_config("body", "No content")

        creds_data = await self.get_credential("credentials_id") or await self.get_credential("google_oauth")
        if not creds_data:
            return {"status": "error", "error": "Gmail OAuth credentials are required.", "data": None}

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
            
            return {
                "status": "success", 
                "data": {
                    "id": send_resp.get("id"), 
                    "recipient": recipient,
                    "subject": subject
                }
            }
        except Exception as e:
            return {"status": "error", "error": f"Gmail Send Failed: {str(e)}", "data": None}

@register_node("gmail_message_fetch")
class GmailFetchMessagesNode(BaseNode):
    """Fetches recent messages from Gmail inbox."""
    node_type = "gmail_message_fetch"
    version = "1.0.0"
    category = "communication"
    credentials_required = ["google_oauth"]

    inputs = {
        "max_results": {"type": "number", "default": 5},
        "query": {"type": "string", "description": "Gmail search query (e.g. 'label:inbox')"}
    }
    outputs = {
        "messages": {"type": "list"},
        "status": {"type": "string"}
    }

    async def execute(self, input_data: Any, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        max_results = self.get_config("max_results", 5)
        query = self.get_config("query", "")
        
        creds_data = await self.get_credential("credentials_id") or await self.get_credential("google_oauth")
        
        if not creds_data:
            return {"status": "error", "error": "Gmail OAuth credentials are required.", "data": None}

        try:
            creds = Credentials.from_authorized_user_info(creds_data)
            service = build("gmail", "v1", credentials=creds)
            
            results = service.users().messages().list(userId="me", maxResults=max_results, q=query).execute()
            messages = results.get('messages', [])
            
            output_list = []
            for msg in messages:
                m = service.users().messages().get(userId='me', id=msg['id']).execute()
                snippet = m.get('snippet')
                headers = m.get('payload', {}).get('headers', [])
                subject = next((h['value'] for h in headers if h['name'] == 'Subject'), "No Subject")
                sender = next((h['value'] for h in headers if h['name'] == 'From'), "Unknown")
                
                output_list.append({
                    "id": msg['id'],
                    "sender": sender,
                    "subject": subject,
                    "snippet": snippet
                })
                
            return {
                "status": "success",
                "data": {
                    "messages": output_list,
                    "count": len(output_list)
                }
            }
        except Exception as e:
            return {"status": "error", "error": f"Gmail Fetch Failed: {str(e)}", "data": None}