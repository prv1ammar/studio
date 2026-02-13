"""
Box Node - Studio Standard (Universal Method)
Batch 94: Cloud Storage (n8n Critical)
"""
from typing import Any, Dict, Optional, List
import aiohttp
from ...base import BaseNode
from ...registry import register_node

@register_node("box_node")
class BoxNode(BaseNode):
    """
    Manage files and folders in Box via API v2.
    """
    node_type = "box_node"
    version = "1.0.0"
    category = "storage"
    credentials_required = ["box_auth"]

    inputs = {
        "action": {
            "type": "dropdown",
            "default": "list_folder",
            "options": ["list_folder", "download_file", "upload_file", "create_folder", "delete_file"],
            "description": "Box action"
        },
        "folder_id": {
            "type": "string",
            "default": "0",
            "description": "Folder ID (0 for root)"
        },
        "file_id": {
            "type": "string",
            "optional": True
        },
        "filename": {
            "type": "string",
            "optional": True
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
            creds = await self.get_credential("box_auth")
            access_token = creds.get("access_token")
            
            if not access_token:
                return {"status": "error", "error": "Box Access Token required."}

            headers = {
                "Authorization": f"Bearer {access_token}"
            }
            
            # 2. Connect to Real API
            base_url = "https://api.box.com/2.0"
            upload_url = "https://upload.box.com/api/2.0"
            action = self.get_config("action", "list_folder")

            async with aiohttp.ClientSession() as session:
                if action == "list_folder":
                    folder_id = self.get_config("folder_id", "0")
                    url = f"{base_url}/folders/{folder_id}/items"
                    async with session.get(url, headers=headers) as resp:
                        if resp.status != 200:
                            return {"status": "error", "error": f"Box API Error: {resp.status}"}
                        res_data = await resp.json()
                        return {"status": "success", "data": {"result": res_data.get("entries", [])}}

                elif action == "download_file":
                    file_id = self.get_config("file_id")
                    if not file_id:
                        return {"status": "error", "error": "file_id required"}
                    
                    url = f"{base_url}/files/{file_id}/content"
                    async with session.get(url, headers=headers) as resp:
                        if resp.status != 200:
                            return {"status": "error", "error": f"Box API Error: {resp.status}"}
                        content = await resp.text()  # Assuming text content for now
                        return {"status": "success", "data": {"result": content}}

                elif action == "upload_file":
                    folder_id = self.get_config("folder_id", "0")
                    filename = self.get_config("filename")
                    content = self.get_config("content") or str(input_data)
                    
                    if not filename:
                        return {"status": "error", "error": "filename required"}
                    
                    url = f"{upload_url}/files/content"
                    # Multipart upload requires a bit more setup in aiohttp
                    data = aiohttp.FormData()
                    data.add_field('attributes', json.dumps({"name": filename, "parent": {"id": folder_id}}))
                    data.add_field('file', content, filename=filename)
                    
                    async with session.post(url, headers=headers, data=data) as resp:
                        if resp.status != 201:
                            return {"status": "error", "error": f"Box API Error: {resp.status}"}
                        res_data = await resp.json()
                        return {"status": "success", "data": {"result": res_data.get("entries", [])[0]}}

                elif action == "create_folder":
                    folder_id = self.get_config("folder_id", "0")
                    name = self.get_config("filename")  # Reusing filename as folder name for simplicity
                    
                    if not name:
                        return {"status": "error", "error": "Folder name (filename) required"}
                    
                    url = f"{base_url}/folders"
                    payload = {"name": name, "parent": {"id": folder_id}}
                    async with session.post(url, headers=headers, json=payload) as resp:
                        if resp.status != 201:
                            return {"status": "error", "error": f"Box API Error: {resp.status}"}
                        res_data = await resp.json()
                        return {"status": "success", "data": {"result": res_data}}

                return {"status": "error", "error": f"Unsupported action: {action}"}

        except Exception as e:
            return {"status": "error", "error": f"Box Node Failed: {str(e)}"}
