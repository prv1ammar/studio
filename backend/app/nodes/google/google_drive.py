from typing import Any, Dict, Optional, List
from pydantic import Field
from app.nodes.base import BaseNode, NodeConfig
from app.nodes.registry import register_node
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
import io
from googleapiclient.http import MediaIoBaseDownload

class GoogleDriveConfig(NodeConfig):
    document_id: Optional[str] = Field(None, description="The ID of the Google Drive document")
    credentials_id: Optional[str] = Field(None, description="Google OAuth Token Credentials ID")

@register_node("google_drive_loader")
class GoogleDriveLoaderNode(BaseNode):
    node_id = "google_drive_loader"
    config_model = GoogleDriveConfig

    async def execute(self, input_data: Any, context: Optional[Dict[str, Any]] = None) -> Any:
        doc_id = self.get_config("document_id") or (input_data if isinstance(input_data, str) else None)
        creds_data = await self.get_credential("credentials_id")
        
        if not creds_data or not doc_id:
            return {"error": "Google Credentials and Document ID are required."}

        try:
            creds = Credentials.from_authorized_user_info(creds_data)
            service = build('drive', 'v3', credentials=creds)

            # Get file metadata
            file_metadata = service.files().get(fileId=doc_id).execute()
            mime_type = file_metadata.get('mimeType')

            # If it's a Google Doc, export it as text
            if mime_type == 'application/vnd.google-apps.document':
                request = service.files().export_media(fileId=doc_id, mimeType='text/plain')
            else:
                request = service.files().get_media(fileId=doc_id)

            fh = io.BytesIO()
            downloader = MediaIoBaseDownload(fh, request)
            done = False
            while done is False:
                status, done = downloader.next_chunk()
            
            content = fh.getvalue().decode('utf-8')
            return {
                "name": file_metadata.get('name'),
                "content": content,
                "mime_type": mime_type
            }
        except Exception as e:
            return {"error": f"Google Drive Load Failed: {str(e)}"}
