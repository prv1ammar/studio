"""
OneDrive Node - Studio Standard (Universal Method)
Batch 107: Cloud Storage
"""
from typing import Any, Dict, Optional
import aiohttp
from ...base import BaseNode
from ...registry import register_node

@register_node("onedrive_node")
class OneDriveNode(BaseNode):
    """
    Microsoft OneDrive integration via Graph API.
    """
    node_type = "onedrive_node"
    version = "1.0.0"
    category = "storage"
    credentials_required = ["microsoft_graph_auth"]

    inputs = {
        "action": {
            "type": "dropdown",
            "default": "upload_file",
            "options": ["upload_file", "list_drive", "list_children", "create_folder"],
            "description": "OneDrive action"
        },
        "path": {
            "type": "string",
            "optional": True,
            "description": "Path or item ID"
        },
        "file_content": {
            "type": "string",
            "optional": True
        },
        "file_name": {
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
            creds = await self.get_credential("microsoft_graph_auth")
            access_token = creds.get("access_token")
            
            if not access_token:
                return {"status": "error", "error": "OneDrive access token required"}

            base_url = "https://graph.microsoft.com/v1.0/me/drive"
            headers = {
                "Authorization": f"Bearer {access_token}"
            }
            
            action = self.get_config("action", "upload_file")

            async with aiohttp.ClientSession() as session:
                if action == "upload_file":
                    file_name = self.get_config("file_name")
                    file_content = self.get_config("file_content")
                    folder_path = self.get_config("path", "")
                    
                    if not file_name or file_content is None:
                        return {"status": "error", "error": "file_name and file_content required"}
                    
                    # Upload small files directly (for simplicity)
                    # For larger files, create upload session is needed
                    target_url = f"{base_url}/root:/{folder_path}/{file_name}:/content" if folder_path else f"{base_url}/root:/{file_name}:/content"
                    
                    upload_headers = headers.copy()
                    upload_headers["Content-Type"] = "text/plain" # Or octet-stream
                    
                    async with session.put(target_url, headers=upload_headers, data=file_content) as resp:
                        if resp.status not in [200, 201]:
                            error_text = await resp.text()
                            return {"status": "error", "error": f"OneDrive API Error {resp.status}: {error_text}"}
                        res_data = await resp.json()
                        return {"status": "success", "data": {"result": res_data}}

                elif action == "list_drive":
                    target_url = f"{base_url}/root/children"
                    async with session.get(target_url, headers=headers) as resp:
                        if resp.status != 200:
                            error_text = await resp.text()
                            return {"status": "error", "error": f"OneDrive API Error {resp.status}: {error_text}"}
                        res_data = await resp.json()
                        return {"status": "success", "data": {"result": res_data.get("value", [])}}
                
                elif action == "create_folder":
                    folder_name = self.get_config("file_name") # Reuse input
                    parent_id = self.get_config("path") # Use path as parent ID or assume root
                    
                    if not folder_name:
                         return {"status": "error", "error": "Folder name (file_name) required"}
                    
                    target_url = f"{base_url}/items/{parent_id}/children" if parent_id else f"{base_url}/root/children"
                    
                    payload = {
                        "name": folder_name,
                        "folder": {},
                        "@microsoft.graph.conflictBehavior": "rename"
                    }
                    
                    create_headers = headers.copy()
                    create_headers["Content-Type"] = "application/json"
                    
                    async with session.post(target_url, headers=create_headers, json=payload) as resp:
                         if resp.status != 201:
                            error_text = await resp.text()
                            return {"status": "error", "error": f"OneDrive API Error {resp.status}: {error_text}"}
                         res_data = await resp.json()
                         return {"status": "success", "data": {"result": res_data}}

            return {"status": "error", "error": f"Unsupported action: {action}"}

        except Exception as e:
            return {"status": "error", "error": f"OneDrive Node Failed: {str(e)}"}
