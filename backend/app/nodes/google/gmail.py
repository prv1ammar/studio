import base64
import json
import re
from collections.abc import Iterator
from json.decoder import JSONDecodeError
from typing import Any, Dict, Optional, List

from google.auth.exceptions import RefreshError
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from langchain_core.chat_sessions import ChatSession
from langchain_core.messages import HumanMessage
try:
    from langchain_google_community.gmail.loader import GMailLoader
except ImportError:
    print("⚠️ Warning: 'langchain_google_community' not found. Gmail Loader will be disabled, but Gmail Sender (gmailNode) remains available.")
    GMailLoader = object # Dummy for class definition

try:
    from lfx.custom.custom_component.component import Component
    from lfx.inputs.inputs import MessageTextInput
    from lfx.io import SecretStrInput
    from lfx.log.logger import logger
    from lfx.schema.data import Data
    from lfx.template.field.base import Output
    LFX_AVAILABLE = True
except ImportError as e:
    print(f"⚠️ Warning: 'lfx' dependencies missing ({e}). Gmail Loader component will be disabled.")
    LFX_AVAILABLE = False
    # Create dummy classes to prevent NameError
    class Component: pass
    def MessageTextInput(**kwargs): return None
    def SecretStrInput(**kwargs): return None
    class logger:
        @staticmethod
        def warning(msg): print(f"LOG: {msg}")
        @staticmethod
        def exception(msg): print(f"LOG: {msg}")
    class Data: pass
    def Output(**kwargs): return None

from ..base import BaseNode
from ..registry import register_node


class GmailLoaderComponent(Component):
    display_name = "Gmail Loader"
    description = "Loads emails from Gmail using provided credentials."
    icon = "Google"
    legacy: bool = True

    inputs = [
        SecretStrInput(
            name="json_string",
            display_name="JSON String of the Service Account Token",
            info="JSON string containing OAuth 2.0 access token information for service account access",
            required=True,
            value="""{
                "account": "",
                "client_id": "",
                "client_secret": "",
                "expiry": "",
                "refresh_token": "",
                "scopes": [
                    "https://www.googleapis.com/auth/gmail.readonly",
                ],
                "token": "",
                "token_uri": "https://oauth2.googleapis.com/token",
                "universe_domain": "googleapis.com"
            }""",
        ),
        MessageTextInput(
            name="label_ids",
            display_name="Label IDs",
            info="Comma-separated list of label IDs to filter emails.",
            required=True,
            value="INBOX,SENT,UNREAD,IMPORTANT",
        ),
        MessageTextInput(
            name="max_results",
            display_name="Max Results",
            info="Maximum number of emails to load.",
            required=True,
            value="10",
        ),
    ]

    outputs = [
        Output(display_name="Data", name="data", method="load_emails"),
    ]

    def load_emails(self) -> Data:
        class CustomGMailLoader(GMailLoader):
            def __init__(
                self, creds: Any, *, n: int = 100, label_ids: list[str] | None = None, raise_error: bool = False
            ) -> None:
                super().__init__(creds, n, raise_error)
                self.label_ids = label_ids if label_ids is not None else ["SENT"]

            def clean_message_content(self, message):
                # Remove URLs
                message = re.sub(r"http\S+|www\S+|https\S+", "", message, flags=re.MULTILINE)

                # Remove email addresses
                message = re.sub(r"\S+@\S+", "", message)

                # Remove special characters and excessive whitespace
                message = re.sub(r"[^A-Za-z0-9\s]+", " ", message)
                message = re.sub(r"\s{2,}", " ", message)

                # Trim leading and trailing whitespace
                return message.strip()

            def _extract_email_content(self, msg: Any) -> HumanMessage:
                from_email = None
                for values in msg["payload"]["headers"]:
                    name = values["name"]
                    if name == "From":
                        from_email = values["value"]
                if from_email is None:
                    msg = "From email not found."
                    raise ValueError(msg)

                parts = msg["payload"]["parts"] if "parts" in msg["payload"] else [msg["payload"]]

                for part in parts:
                    if part["mimeType"] == "text/plain":
                        data = part["body"]["data"]
                        data = base64.urlsafe_b64decode(data).decode("utf-8")
                        pattern = re.compile(r"\r\nOn .+(\r\n)*wrote:\r\n")
                        newest_response = re.split(pattern, data)[0]
                        return HumanMessage(
                            content=self.clean_message_content(newest_response),
                            additional_kwargs={"sender": from_email},
                        )
                msg = "No plain text part found in the email."
                raise ValueError(msg)

            def _get_message_data(self, service: Any, message: Any) -> ChatSession:
                msg = service.users().messages().get(userId="me", id=message["id"]).execute()
                message_content = self._extract_email_content(msg)

                in_reply_to = None
                email_data = msg["payload"]["headers"]
                for values in email_data:
                    name = values["name"]
                    if name == "In-Reply-To":
                        in_reply_to = values["value"]

                thread_id = msg["threadId"]

                if in_reply_to:
                    thread = service.users().threads().get(userId="me", id=thread_id).execute()
                    messages = thread["messages"]

                    response_email = None
                    for _message in messages:
                        email_data = _message["payload"]["headers"]
                        for values in email_data:
                            if values["name"] == "Message-ID":
                                message_id = values["value"]
                                if message_id == in_reply_to:
                                    response_email = _message
                    if response_email is None:
                        msg = "Response email not found in the thread."
                        raise ValueError(msg)
                    starter_content = self._extract_email_content(response_email)
                    return ChatSession(messages=[starter_content, message_content])
                return ChatSession(messages=[message_content])

            def lazy_load(self) -> Iterator[ChatSession]:
                service = build("gmail", "v1", credentials=self.creds)
                results = (
                    service.users().messages().list(userId="me", labelIds=self.label_ids, maxResults=self.n).execute()
                )
                messages = results.get("messages", [])
                if not messages:
                    logger.warning("No messages found with the specified labels.")
                for message in messages:
                    try:
                        yield self._get_message_data(service, message)
                    except Exception:
                        if self.raise_error:
                            raise
                        else:
                            logger.exception(f"Error processing message {message['id']}")

        json_string = self.json_string
        label_ids = self.label_ids.split(",") if self.label_ids else ["INBOX"]
        max_results = int(self.max_results) if self.max_results else 100

        # Load the token information from the JSON string
        try:
            token_info = json.loads(json_string)
        except JSONDecodeError as e:
            msg = "Invalid JSON string"
            raise ValueError(msg) from e

        creds = Credentials.from_authorized_user_info(token_info)

        # Initialize the custom loader with the provided credentials
        loader = CustomGMailLoader(creds=creds, n=max_results, label_ids=label_ids)

        try:
            docs = loader.load()
        except RefreshError as e:
            msg = "Authentication error: Unable to refresh authentication token. Please try to reauthenticate."
            raise ValueError(msg) from e
        except Exception as e:
            msg = f"Error loading documents: {e}"
            raise ValueError(msg) from e

        # Return the loaded documents
        self.status = docs
        return Data(data={"text": docs})


@register_node("gmailNode")
class GmailSendMessageNode(BaseNode):
    """
    Standardized node for sending emails via Google Gmail API.
    Compatible with Studio AgentEngine.
    """
    async def execute(self, input_data: Any, context: Optional[Dict[str, Any]] = None) -> Any:
        # 1. Extract inputs (Compatible with LeadIngestor and Notification ports)
        recipient = None
        message = None
        subject = self.get_config("subject", "Tyboo Real Estate Notification")
        
        if isinstance(input_data, dict):
            recipient = input_data.get("recipient")
            message = input_data.get("message") or input_data.get("input")
        elif isinstance(input_data, str):
            message = input_data

        # Fallback to node-level configuration
        recipient = recipient or self.get_config("recipient") or self.get_config("smtp_user")
        message = message or self.get_config("message")
        
        if not recipient or not message:
             print(f"⚠️ GmailNode Blocked: Missing recipient ({recipient}) or message ({message})")
             return "Error: Missing recipient or message for Gmail."

        # 2. Authentication (Support for Centralized Credentials)
        cred_data = self.get_credential()
        if cred_data:
            token_info = cred_data
            print(f"✅ GmailNode: Using centralized credentials '{self.get_config('credentials_id')}'")
        else:
            json_string = self.get_config("json_string")
            if not json_string:
                 print("❌ GmailNode Error: 'json_string' or 'credentials_id' is missing.")
                 return "Error: Gmail credentials not configured."
            try:
                token_info = json.loads(json_string) if isinstance(json_string, str) else json_string
            except json.JSONDecodeError as e:
                return f"Error: Invalid JSON string in Gmail config: {e}"

        try:
            from email.message import EmailMessage
            import base64
            
            # HELPER: Check if user pasted 'installed' or 'web' from client_secrets.json (wrong format)
            if any(k in token_info for k in ["installed", "web", "client_id"]):
                 if "refresh_token" not in token_info and "token" not in token_info:
                     print("❌ GmailNode Configuration Error: Detected Client Secrets instead of Token.")
                     return "Error: You pasted 'credentials.json' (Client Secret). Please provide the Authorized Token JSON (containing 'refresh_token')."

            creds = Credentials.from_authorized_user_info(token_info)
            service = build("gmail", "v1", credentials=creds)
            
            # 3. Build Email
            email_msg = EmailMessage()
            email_msg.set_content(message)
            email_msg['To'] = recipient
            email_msg['From'] = 'me'
            email_msg['Subject'] = subject
            
            # Encode for Gmail API
            encoded_message = base64.urlsafe_b64encode(email_msg.as_bytes()).decode()
            create_message = {'raw': encoded_message}
            
            # 4. Send
            print(f"🚀 GmailNode: Sending email to {recipient}...")
            send_resp = service.users().messages().send(userId="me", body=create_message).execute()
            
            return f"✅ Gmail successfully sent to {recipient}. Message ID: {send_resp.get('id')}"
            
        except RefreshError:
            print("❌ GmailNode Auth Error: Token expired. Please refresh OAuth credentials.")
            return "Error: Gmail Authentication expired. Please update 'json_string'."
        except Exception as e:
            print(f"❌ GmailNode System Error: {e}")
            return f"Error: Gmail failed - {str(e)}"
