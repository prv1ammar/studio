"""
Dropbox Node - Studio Standard (Universal Method)
Batch 94: Cloud Storage (n8n Critical)
"""
from typing import Any, Dict, Optional, List
import aiohttp
from ...base import BaseNode
from ...registry import register_node

@register_node("dropbox_node")
class DropboxNode(BaseNode):
    """
    Manage files and folders in Dropbox via API v2.
    """
    node_type = "dropbox_node"
    version = "1.0.0"
    category = "storage"
    credentials_required = ["dropbox_auth"]

    inputs = {
        "action": {
            "type": "dropdown",
            "default": "list_folder",
            "options": ["list_folder", "download_file", "upload_file", "create_folder", "delete_file"],
            "description": "Dropbox action"
        },
        "path": {
            "type": "string",
            "description": "Path in Dropbox (e.g. /my-folder/file.txt)"
        },
        "content": {
            "type": "string",
            "optional": True
        }
    }

    outputs = {
        "result": {"type": "any"},
        "status": {"type": "string"}
    }

    async def execute(self, input_data: Any, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        try:
            # 1. Authentication
            creds = await self.get_credential("dropbox_auth")
            access_token = creds.get("access_token")
            
            if not access_token:
                return {"status": "error", "error": "Dropbox Access Token required."}

            headers = {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json"
            }
            
            # 2. Connect to Real API
            base_url = "https://api.dropboxapi.com/2"
            content_url = "https://content.dropboxapi.com/2"
            action = self.get_config("action", "list_folder")

            async with aiohttp.ClientSession() as session:
                if action == "list_folder":
                    path = self.get_config("path", "")
                    if path == "/": path = ""  # Root is empty string for list_folder
                    
                    url = f"{base_url}/files/list_folder"
                    payload = {"path": path}
                    async with session.post(url, headers=headers, json=payload) as resp:
                        if resp.status != 200:
                            return {"status": "error", "error": f"Dropbox API Error: {resp.status}"}
                        res_data = await resp.json()
                        return {"status": "success", "data": {"result": res_data.get("entries", [])}}

                elif action == "download_file":
                    path = self.get_config("path")
                    if not path:
                        return {"status": "error", "error": "path required"}
                    
                    url = f"{content_url}/files/download"
                    headers["Dropbox-API-Arg"] = f'{{"path": "{path}"}}'
                    # Remove Content-Type for download
                    del headers["Content-Type"]
                    
                    async with session.post(url, headers=headers) as resp:
                        if resp.status != 200:
                            return {"status": "error", "error": f"Dropbox API Error: {resp.status}"}
                        content = await resp.text()
                        return {"status": "success", "data": {"result": content}}

                elif action == "upload_file":
                    path = self.get_config("path")
                    content = self.get_config("content") or str(input_data)
                    
                    if not path:
                        return {"status": "error", "error": "path required"}
                    
                    url = f"{content_url}/files/upload"
                    headers["Dropbox-API-Arg"] = f'{{"path": "{path}", "mode": "add", "autorename": true, "mute": false}}'
                    headers["Content-Type"] = "application/octet-stream"
                    
                    async with session.post(url, headers=headers, data=content) as resp:
                        if resp.status != 200:
                            return {"status": "error", "error": f"Dropbox API Error: {resp.status}"}
                        res_data = await resp.json()
                        return {"status": "success", "data": {"result": res_data}}

                elif action == "create_folder":
                    path = self.get_config("path")
                    if not path:
                        return {"status": "error", "error": "path required"}
                    
                    url = f"{base_url}/files/create_folder_v2"
                    payload = {"path": path}
                    async with session.post(url, headers=headers, json=payload) as resp:
                        if resp.status != 200:
                            return {"status": "error", "error": f"Dropbox API Error: {resp.status}"}
                        res_data = await resp.json()
                        return {"status": "success", "data": {"result": res_data.get("metadata", {})}}

                return {"status": "error", "error": f"Unsupported action: {action}"}

        except Exception as e:
            return {"status": "error", "error": f"Dropbox Node Failed: {str(e)}"}
