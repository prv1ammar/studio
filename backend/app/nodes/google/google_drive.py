import io
import json
from typing import Any, Dict, Optional, List
from pydantic import Field
from app.nodes.base import BaseNode, NodeConfig
from app.nodes.registry import register_node
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload, MediaIoBaseUpload

class GoogleDriveConfig(NodeConfig):
    document_id: Optional[str] = Field(None, description="The ID of the Google Drive document")
    query: Optional[str] = Field(None, description="Search query (e.g., name contains 'Report')")
    folder_id: Optional[str] = Field(None, description="Parent folder ID for list/upload")
    file_name: Optional[str] = Field(None, description="Name for the uploaded file")
    credentials_id: Optional[str] = Field(None, description="Google OAuth Token Credentials ID")

@register_node("google_drive_loader")
class GoogleDriveLoaderNode(BaseNode):
    async def execute(self, input_data: Any, context: Optional[Dict[str, Any]] = None) -> Any:
        doc_id = self.get_config("document_id") or (input_data if isinstance(input_data, str) else None)
        creds_data = await self.get_credential("credentials_id")
        
        if not creds_data or not doc_id:
            return {"error": "Google Credentials and Document ID are required."}

        try:
            creds = Credentials.from_authorized_user_info(creds_data)
            service = build('drive', 'v3', credentials=creds)

            file_metadata = service.files().get(fileId=doc_id).execute()
            mime_type = file_metadata.get('mimeType')

            if mime_type == 'application/vnd.google-apps.document':
                request = service.files().export_media(fileId=doc_id, mimeType='text/plain')
            else:
                request = service.files().get_media(fileId=doc_id)

            fh = io.BytesIO()
            downloader = MediaIoBaseDownload(fh, request)
            done = False
            while done is False:
                status, done = downloader.next_chunk()
            
            try:
                content = fh.getvalue().decode('utf-8')
            except:
                # If decode fails, it's binary content
                content = f"Binary content ({len(fh.getvalue())} bytes)"
                
            return {
                "id": doc_id,
                "name": file_metadata.get('name'),
                "content": content,
                "mime_type": mime_type
            }
        except Exception as e:
            return {"error": f"Google Drive Load Failed: {str(e)}"}

@register_node("google_drive_search")
class GoogleDriveSearchNode(BaseNode):
    async def execute(self, input_data: Any, context: Optional[Dict[str, Any]] = None) -> Any:
        query = self.get_config("query") or (input_data if isinstance(input_data, str) else "")
        creds_data = await self.get_credential("credentials_id")
        
        if not creds_data:
            return {"error": "Google Credentials are required."}

        try:
            creds = Credentials.from_authorized_user_info(creds_data)
            service = build('drive', 'v3', credentials=creds)

            # Construct query: name contains '...'
            q = f"name contains '{query}'" if query and " " not in query and "=" not in query else query
            
            results = service.files().list(
                q=q, 
                pageSize=10, 
                fields="files(id, name, mimeType, webViewLink)"
            ).execute()
            
            return results.get("files", [])
        except Exception as e:
            return {"error": f"Google Drive Search Failed: {str(e)}"}

@register_node("google_drive_uploader")
class GoogleDriveUploaderNode(BaseNode):
    async def execute(self, input_data: Any, context: Optional[Dict[str, Any]] = None) -> Any:
        file_name = self.get_config("file_name") or "Studio_Upload.txt"
        folder_id = self.get_config("folder_id")
        creds_data = await self.get_credential("credentials_id")
        
        if not creds_data:
            return {"error": "Google Credentials are required."}

        try:
            creds = Credentials.from_authorized_user_info(creds_data)
            service = build('drive', 'v3', credentials=creds)

            # Check if input_data is content (str) or a dict with metadata
            content = input_data
            if isinstance(input_data, dict):
                content = input_data.get("content", str(input_data))
                file_name = input_data.get("file_name", file_name)

            file_metadata = {'name': file_name}
            if folder_id:
                file_metadata['parents'] = [folder_id]

            media = MediaIoBaseUpload(
                io.BytesIO(content.encode('utf-8')), 
                mimetype='text/plain', 
                resumable=True
            )
            
            file = service.files().create(
                body=file_metadata,
                media_body=media,
                fields='id, webViewLink'
            ).execute()
            
            return {
                "status": "success",
                "file_id": file.get("id"),
                "url": file.get("webViewLink")
            }
        except Exception as e:
            return {"error": f"Google Drive Upload Failed: {str(e)}"}

@register_node("google_drive_list")
class GoogleDriveListNode(BaseNode):
    async def execute(self, input_data: Any, context: Optional[Dict[str, Any]] = None) -> Any:
        folder_id = self.get_config("folder_id") or "root"
        creds_data = await self.get_credential("credentials_id")
        
        if not creds_data:
            return {"error": "Google Credentials are required."}

        try:
            creds = Credentials.from_authorized_user_info(creds_data)
            service = build('drive', 'v3', credentials=creds)

            q = f"'{folder_id}' in parents and trashed = false"
            results = service.files().list(
                q=q,
                pageSize=20,
                fields="files(id, name, mimeType)"
            ).execute()
            
            return results.get("files", [])
        except Exception as e:
            return {"error": f"Google Drive List Failed: {str(e)}"}
