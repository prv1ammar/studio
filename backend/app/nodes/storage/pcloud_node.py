"""
pCloud Node - Studio Standard (Universal Method)
Batch 107: Cloud Storage
"""
from typing import Any, Dict, Optional
import aiohttp
from ..base import BaseNode
from ..registry import register_node

@register_node("pcloud_node")
class PCloudNode(BaseNode):
    """
    pCloud cloud storage integration.
    """
    node_type = "pcloud_node"
    version = "1.0.0"
    category = "storage"
    credentials_required = ["pcloud_auth"]


    properties = [
        {
            'displayName': 'Operation',
            'name': 'operation',
            'type': 'options',
            'default': 'upload_file',
            'options': [
                {'name': 'Upload File', 'value': 'upload_file'},
                {'name': 'List Folder', 'value': 'list_folder'},
                {'name': 'Create Folder', 'value': 'create_folder'},
            ],
            'description': 'pCloud action',
        },
        {
            'displayName': 'File Content',
            'name': 'file_content',
            'type': 'string',
            'default': '',
        },
        {
            'displayName': 'Filename',
            'name': 'filename',
            'type': 'string',
            'default': '',
        },
        {
            'displayName': 'Folder Id',
            'name': 'folder_id',
            'type': 'string',
            'default': '0',
            'description': 'Root folder ID is 0',
        },
        {
            'displayName': 'Name',
            'name': 'name',
            'type': 'string',
            'default': '',
            'description': 'Folder name',
        },
    ]
    inputs = {
        "action": {
            "type": "dropdown",
            "default": "upload_file",
            "options": ["upload_file", "list_folder", "create_folder"],
            "description": "pCloud action"
        },
        "folder_id": {
            "type": "string",
            "default": "0",
            "optional": True,
            "description": "Root folder ID is 0"
        },
        "filename": {
            "type": "string",
            "optional": True
        },
        "file_content": {
            "type": "string",
            "optional": True
        },
        "name": {
            "type": "string",
            "optional": True,
            "description": "Folder name"
        }
    }

    outputs = {
        "result": {"type": "any"},
        "status": {"type": "string"}
    }

    async def execute(self, input_data: Any, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        try:
            creds = await self.get_credential("pcloud_auth")
            access_token = creds.get("access_token")
            # pCloud can use US or EU API
            region = creds.get("region", "US").upper()
            base_url = "https://api.pcloud.com" if region == "US" else "https://eapi.pcloud.com"

            if not access_token:
                return {"status": "error", "error": "pCloud access token required"}

            action = self.get_config("action", "upload_file")
            folder_id = self.get_config("folder_id", "0")

            params = {"access_token": access_token}

            async with aiohttp.ClientSession() as session:
                if action == "upload_file":
                    # Uses uploadfile endpoint
                    upload_url = f"{base_url}/uploadfile"
                    filename = self.get_config("filename")
                    file_content = self.get_config("file_content")
                    
                    if not filename or file_content is None:
                         return {"status": "error", "error": "filename and file_content required"}
                    
                    upload_params = params.copy()
                    upload_params["folderid"] = folder_id
                    upload_params["filename"] = filename
                    
                    # Multipart upload
                    data = aiohttp.FormData()
                    data.add_field('file', file_content, filename=filename) # Content can be bytes or string
                    
                    async with session.post(upload_url, params=upload_params, data=data) as resp:
                         res_data = await resp.json()
                         if res_data.get("result", 1) != 0: # 0 is success
                             return {"status": "error", "error": f"pCloud Error: {res_data}"}
                         return {"status": "success", "data": {"result": res_data}}
                
                elif action == "list_folder":
                    list_url = f"{base_url}/listfolder"
                    list_params = params.copy()
                    list_params["folderid"] = folder_id
                    
                    async with session.get(list_url, params=list_params) as resp:
                         res_data = await resp.json()
                         if res_data.get("result", 1) != 0:
                             return {"status": "error", "error": f"pCloud Error: {res_data}"}
                         # Returning contents
                         return {"status": "success", "data": {"result": res_data.get("metadata", {}).get("contents", [])}}

                elif action == "create_folder":
                    create_url = f"{base_url}/createfolder"
                    folder_name = self.get_config("name")
                    if not folder_name:
                         return {"status": "error", "error": "Folder name required"}
                         
                    create_params = params.copy()
                    create_params["folderid"] = folder_id
                    create_params["name"] = folder_name
                    
                    async with session.post(create_url, params=create_params) as resp:
                        res_data = await resp.json()
                        if res_data.get("result", 1) != 0:
                             return {"status": "error", "error": f"pCloud Error: {res_data}"}
                        return {"status": "success", "data": {"result": res_data}}

            return {"status": "error", "error": f"Unsupported action: {action}"}

        except Exception as e:
            return {"status": "error", "error": f"pCloud Node Failed: {str(e)}"}