"""
Box Node - Studio Standard (Universal Method)
Batch 107: Cloud Storage
"""
from typing import Any, Dict, Optional
import aiohttp
from ...base import BaseNode
from ...registry import register_node

@register_node("box_node")
class BoxNode(BaseNode):
    """
    Box integration for enterprise content management.
    """
    node_type = "box_node"
    version = "1.0.0"
    category = "storage"
    credentials_required = ["box_auth"]

    inputs = {
        "action": {
            "type": "dropdown",
            "default": "upload_file",
            "options": ["upload_file", "list_folder", "create_folder", "get_file_info"],
            "description": "Box action"
        },
        "folder_id": {
            "type": "string",
            "default": "0",
            "optional": True,
            "description": "Root folder ID is 0"
        },
        "file_name": {
            "type": "string",
            "optional": True
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
            creds = await self.get_credential("box_auth")
            access_token = creds.get("access_token")
            
            if not access_token:
                return {"status": "error", "error": "Box access token required"}

            api_url = "https://api.box.com/2.0"
            upload_url = "https://upload.box.com/api/2.0"
            
            headers = {"Authorization": f"Bearer {access_token}"}
            
            action = self.get_config("action", "upload_file")
            folder_id = self.get_config("folder_id", "0")

            async with aiohttp.ClientSession() as session:
                if action == "upload_file":
                    file_name = self.get_config("file_name")
                    file_content = self.get_config("file_content")
                    
                    if not file_name or file_content is None:
                        return {"status": "error", "error": "file_name and file_content required"}
                    
                    # Box upload needs attributes part + file content part (multipart/form-data logic)
                    # Simplified for text files/strings here
                    data = aiohttp.FormData()
                    data.add_field('attributes', f'{{"name": "{file_name}", "parent": {{"id": "{folder_id}"}}}}')
                    data.add_field('file', file_content, filename=file_name, content_type='text/plain')
                    
                    async with session.post(f"{upload_url}/files/content", headers=headers, data=data) as resp:
                         if resp.status != 201:
                            error_text = await resp.text()
                            return {"status": "error", "error": f"Box API Error {resp.status}: {error_text}"}
                         res_data = await resp.json()
                         return {"status": "success", "data": {"result": res_data}}

                elif action == "list_folder":
                    async with session.get(f"{api_url}/folders/{folder_id}/items", headers=headers) as resp:
                        if resp.status != 200:
                            error_text = await resp.text()
                            return {"status": "error", "error": f"Box API Error {resp.status}: {error_text}"}
                        res_data = await resp.json()
                        return {"status": "success", "data": {"result": res_data.get("entries", [])}}
                
                elif action == "create_folder":
                    folder_name = self.get_config("file_name") # Reusing input for name
                    if not folder_name:
                         return {"status": "error", "error": "Folder name (file_name input) required"}
                         
                    payload = {"name": folder_name, "parent": {"id": folder_id}}
                    async with session.post(f"{api_url}/folders", headers=headers, json=payload) as resp:
                        if resp.status != 201:
                            error_text = await resp.text()
                            return {"status": "error", "error": f"Box API Error {resp.status}: {error_text}"}
                        res_data = await resp.json()
                        return {"status": "success", "data": {"result": res_data}}

            return {"status": "error", "error": f"Unsupported action: {action}"}

        except Exception as e:
            return {"status": "error", "error": f"Box Node Failed: {str(e)}"}
