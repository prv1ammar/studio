"""
Dropbox Node - Studio Standard (Universal Method)
Batch 107: Cloud Storage
"""
from typing import Any, Dict, Optional
import aiohttp
from ...base import BaseNode
from ...registry import register_node

@register_node("dropbox_node")
class DropboxNode(BaseNode):
    """
    Dropbox integration for file storage and sharing.
    """
    node_type = "dropbox_node"
    version = "1.0.0"
    category = "storage"
    credentials_required = ["dropbox_auth"]

    inputs = {
        "action": {
            "type": "dropdown",
            "default": "upload_file",
            "options": ["upload_file", "download_file", "list_folder", "create_folder", "delete_file"],
            "description": "Dropbox action"
        },
        "path": {
            "type": "string",
            "optional": True,
            "description": "Path in Dropbox (e.g. /folder/file.txt)"
        },
        "file_content": {
            "type": "string",
            "optional": True,
            "description": "Content to upload"
        }
    }

    outputs = {
        "result": {"type": "any"},
        "status": {"type": "string"}
    }

    async def execute(self, input_data: Any, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        try:
            creds = await self.get_credential("dropbox_auth")
            access_token = creds.get("access_token")
            
            if not access_token:
                return {"status": "error", "error": "Dropbox access token required"}

            api_url = "https://api.dropboxapi.com/2"
            content_url = "https://content.dropboxapi.com/2"
            
            headers = {"Authorization": f"Bearer {access_token}"}
            
            action = self.get_config("action", "upload_file")
            path = self.get_config("path")
            
            if not path and action != "list_folder": # list_folder can list root with empty path
                 return {"status": "error", "error": "path required"}

            async with aiohttp.ClientSession() as session:
                if action == "upload_file":
                    file_content = self.get_config("file_content")
                    if file_content is None:
                        return {"status": "error", "error": "file_content required"}
                    
                    # Upload requires content-type application/octet-stream usually and specific header
                    upload_headers = {
                        "Authorization": f"Bearer {access_token}",
                        "Dropbox-API-Arg": f'{{"path": "{path}", "mode": "add", "autorename": true, "mute": false}}',
                        "Content-Type": "application/octet-stream"
                    }
                    
                    async with session.post(f"{content_url}/files/upload", headers=upload_headers, data=file_content) as resp:
                         if resp.status != 200:
                            error_text = await resp.text()
                            return {"status": "error", "error": f"Dropbox API Error {resp.status}: {error_text}"}
                         res_data = await resp.json()
                         return {"status": "success", "data": {"result": res_data}}

                elif action == "list_folder":
                    list_headers = {
                        "Authorization": f"Bearer {access_token}",
                        "Content-Type": "application/json"
                    }
                    # Default empty path to root ""
                    folder_path = path if path else ""
                    payload = {"path": folder_path}
                    
                    async with session.post(f"{api_url}/files/list_folder", headers=list_headers, json=payload) as resp:
                        if resp.status != 200:
                            error_text = await resp.text()
                            return {"status": "error", "error": f"Dropbox API Error {resp.status}: {error_text}"}
                        res_data = await resp.json()
                        return {"status": "success", "data": {"result": res_data.get("entries", [])}}
                
                elif action == "create_folder":
                    create_headers = {
                        "Authorization": f"Bearer {access_token}",
                        "Content-Type": "application/json"
                    }
                    payload = {"path": path}
                    async with session.post(f"{api_url}/files/create_folder_v2", headers=create_headers, json=payload) as resp:
                        if resp.status != 200:
                            error_text = await resp.text()
                            return {"status": "error", "error": f"Dropbox API Error {resp.status}: {error_text}"}
                        res_data = await resp.json()
                        return {"status": "success", "data": {"result": res_data}}

            return {"status": "error", "error": f"Unsupported action: {action}"}

        except Exception as e:
            return {"status": "error", "error": f"Dropbox Node Failed: {str(e)}"}
