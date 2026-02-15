"""
Google Cloud Storage Node - Studio Standard (Universal Method)
Batch 107: Cloud Storage
"""
from typing import Any, Dict, Optional
import aiohttp
from ...base import BaseNode
from ...registry import register_node

@register_node("google_cloud_storage_node")
class GoogleCloudStorageNode(BaseNode):
    """
    Google Cloud Storage integration for object storage.
    """
    node_type = "google_cloud_storage_node"
    version = "1.0.0"
    category = "storage"
    credentials_required = ["google_cloud_storage_auth"]

    inputs = {
        "action": {
            "type": "dropdown",
            "default": "upload_file",
            "options": ["upload_file", "download_file", "list_buckets", "list_objects", "delete_object"],
            "description": "GCS action"
        },
        "bucket_name": {
            "type": "string",
            "optional": True
        },
        "object_name": {
            "type": "string",
            "optional": True
        },
        "file_content": {
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
            creds = await self.get_credential("google_cloud_storage_auth")
            access_token = creds.get("access_token")
            # Note: Production would use Google Auth library logic, simplified here with token assumption
            
            if not access_token:
                return {"status": "error", "error": "Google Cloud access token required"}

            base_url = "https://storage.googleapis.com/storage/v1"
            upload_url = "https://storage.googleapis.com/upload/storage/v1"
            
            headers = {"Authorization": f"Bearer {access_token}"}
            
            action = self.get_config("action", "upload_file")

            async with aiohttp.ClientSession() as session:
                if action == "upload_file":
                    bucket = self.get_config("bucket_name")
                    name = self.get_config("object_name")
                    content = self.get_config("file_content")
                    
                    if not bucket or not name or content is None:
                        return {"status": "error", "error": "bucket_name, object_name, and file_content required"}
                    
                    params = {"uploadType": "media", "name": name}
                    url = f"{upload_url}/b/{bucket}/o"
                    
                    headers["Content-Type"] = "text/plain" # Or appropriate type
                    
                    async with session.post(url, headers=headers, params=params, data=content) as resp:
                         if resp.status != 200:
                            error_text = await resp.text()
                            return {"status": "error", "error": f"GCS API Error {resp.status}: {error_text}"}
                         res_data = await resp.json()
                         return {"status": "success", "data": {"result": res_data}}

                elif action == "list_buckets":
                    project_id = creds.get("project_id") # Usually in creds
                    if not project_id:
                        return {"status": "error", "error": "Project ID required in credentials"}
                        
                    params = {"project": project_id}
                    async with session.get(f"{base_url}/b", headers=headers, params=params) as resp:
                        if resp.status != 200:
                            error_text = await resp.text()
                            return {"status": "error", "error": f"GCS API Error {resp.status}: {error_text}"}
                        res_data = await resp.json()
                        return {"status": "success", "data": {"result": res_data.get("items", [])}}

            return {"status": "error", "error": f"Unsupported action: {action}"}

        except Exception as e:
            return {"status": "error", "error": f"GCS Node Failed: {str(e)}"}
