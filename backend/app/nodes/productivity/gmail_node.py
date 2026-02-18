"""
Gmail Integration Node - Studio Standard
Batch 40: Productivity Integrations
"""
from typing import Any, Dict, Optional, List
import base64
from email.message import EmailMessage
from ..base import BaseNode
from ..registry import register_node

@register_node("gmail_node")
class GmailNode(BaseNode):
    """
    Manage emails via Gmail API.
    Supports: Send Email, Read Emails, Create Draft.
    Requires Google OAuth credentials.
    """
    node_type = "gmail_node"
    version = "1.0.0"
    category = "productivity"
    credentials_required = ["google_oauth"]


    properties = [
        {
            'displayName': 'Operation',
            'name': 'operation',
            'type': 'options',
            'default': 'read_emails',
            'options': [
                {'name': 'Read Emails', 'value': 'read_emails'},
                {'name': 'Send Email', 'value': 'send_email'},
                {'name': 'Create Draft', 'value': 'create_draft'},
            ],
            'description': 'Action to perform',
        },
        {
            'displayName': 'Body',
            'name': 'body',
            'type': 'string',
            'default': '',
            'description': 'Email body content',
        },
        {
            'displayName': 'Max Results',
            'name': 'max_results',
            'type': 'string',
            'default': 5,
            'description': 'Max emails to retrieve',
        },
        {
            'displayName': 'Query',
            'name': 'query',
            'type': 'string',
            'default': '',
            'description': 'Search query for reading emails (e.g., 'is:unread')',
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
            'description': 'Email subject',
        },
    ]
    inputs = {
        "action": {
            "type": "dropdown",
            "default": "read_emails",
            "options": ["read_emails", "send_email", "create_draft"],
            "description": "Action to perform"
        },
        "query": {
            "type": "string",
            "description": "Search query for reading emails (e.g., 'is:unread')"
        },
        "max_results": {
            "type": "number",
            "default": 5,
            "description": "Max emails to retrieve"
        },
        "recipient": {
            "type": "string",
            "description": "Recipient email address"
        },
        "subject": {
            "type": "string",
            "description": "Email subject"
        },
        "body": {
            "type": "string",
            "description": "Email body content"
        }
    }

    outputs = {
        "messages": {"type": "array"},
        "result": {"type": "object"},
        "id": {"type": "string"}
    }

    async def execute(self, input_data: Any, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        try:
            # Check dependency
            try:
                from google.oauth2.credentials import Credentials
                from googleapiclient.discovery import build
            except ImportError:
                return {"status": "error", "error": "google-api-python-client not installed."}

            # Get Creds
            creds_data = await self.get_credential("google_oauth")
            if not creds_data:
                return {"status": "error", "error": "Google OAuth credentials are required."}
            
            # Helper to build service
            def get_service(creds_info):
                creds = Credentials.from_authorized_user_info(creds_info)
                return build("gmail", "v1", credentials=creds)

            service = get_service(creds_data)
            action = self.get_config("action", "read_emails")
            result_data = {}

            if action == "read_emails":
                query = self.get_config("query", "")
                max_results = int(self.get_config("max_results", 5))
                
                # List messages
                results = service.users().messages().list(userId="me", maxResults=max_results, q=query).execute()
                messages = results.get('messages', [])
                
                output_list = []
                for msg in messages:
                    # Get full details
                    m = service.users().messages().get(userId='me', id=msg['id']).execute()
                    snippet = m.get('snippet')
                    payload = m.get('payload', {})
                    headers = payload.get('headers', [])
                    
                    subject = next((h['value'] for h in headers if h['name'] == 'Subject'), "No Subject")
                    sender = next((h['value'] for h in headers if h['name'] == 'From'), "Unknown")
                    date = next((h['value'] for h in headers if h['name'] == 'Date'), "Unknown")
                    
                    # Extract body (simplified)
                    body = snippet # Fallback
                    if 'parts' in payload:
                        for part in payload['parts']:
                            if part['mimeType'] == 'text/plain':
                                data = part['body'].get('data')
                                if data:
                                    body = base64.urlsafe_b64decode(data).decode()
                                    break
                    elif 'body' in payload:
                        data = payload['body'].get('data')
                        if data:
                            body = base64.urlsafe_b64decode(data).decode()

                    output_list.append({
                        "id": msg['id'],
                        "sender": sender,
                        "subject": subject,
                        "date": date,
                        "snippet": snippet,
                        "body": body
                    })
                
                result_data = {
                    "messages": output_list,
                    "count": len(output_list)
                }

            elif action in ["send_email", "create_draft"]:
                recipient = self.get_config("recipient")
                subject = self.get_config("subject", "No Subject")
                body = self.get_config("body", "")
                
                # Handle input overrides
                if isinstance(input_data, dict):
                    recipient = input_data.get("recipient") or input_data.get("to") or recipient
                    subject = input_data.get("subject") or subject
                    body = input_data.get("body") or input_data.get("content") or body
                elif isinstance(input_data, str) and input_data:
                    body = input_data
                
                if not recipient and action == "send_email":
                     return {"status": "error", "error": "Recipient is required to send email."}

                # Create email message
                email_msg = EmailMessage()
                email_msg.set_content(body)
                if recipient:
                    email_msg['To'] = recipient
                email_msg['From'] = 'me'
                email_msg['Subject'] = subject
                
                encoded_message = base64.urlsafe_b64encode(email_msg.as_bytes()).decode()
                create_message = {'raw': encoded_message}

                if action == "send_email":
                    send_resp = service.users().messages().send(userId="me", body=create_message).execute()
                    result_data = {
                        "id": send_resp.get("id"),
                        "label_ids": send_resp.get("labelIds"),
                        "thread_id": send_resp.get("threadId"),
                        "status": "sent"
                    }
                else: # create_draft
                    draft_body = {'message': create_message}
                    draft_resp = service.users().drafts().create(userId="me", body=draft_body).execute()
                    result_data = {
                        "id": draft_resp.get("id"),
                        "message_id": draft_resp.get("message", {}).get("id"),
                        "status": "draft_created"
                    }

            else:
                 return {"status": "error", "error": f"Unknown action: {action}"}

            return {
                "status": "success",
                "data": result_data
            }

        except Exception as e:
            return {"status": "error", "error": f"Gmail Operation Failed: {str(e)}"}