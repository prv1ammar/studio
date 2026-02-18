"""
Google Cloud Storage Node - Studio Standard (Universal Method)
Batch 94: Cloud Storage (n8n Critical)
"""
from typing import Any, Dict, Optional, List
import aiohttp
from ..base import BaseNode
from ..registry import register_node

@register_node("gcs_node")
class GCSNode(BaseNode):
    """
    Manage objects in Google Cloud Storage buckets via JSON API.
    """
    node_type = "gcs_node"
    version = "1.0.0"
    category = "storage"
    credentials_required = ["google_cloud_auth"]


    properties = [
        {
            'displayName': 'Operation',
            'name': 'operation',
            'type': 'options',
            'default': 'list_buckets',
            'options': [
                {'name': 'List Buckets', 'value': 'list_buckets'},
                {'name': 'List Objects', 'value': 'list_objects'},
                {'name': 'Get Object', 'value': 'get_object'},
                {'name': 'Upload Object', 'value': 'upload_object'},
                {'name': 'Delete Object', 'value': 'delete_object'},
            ],
            'description': 'GCS action',
        },
        {
            'displayName': 'Bucket Name',
            'name': 'bucket_name',
            'type': 'string',
            'default': '',
        },
        {
            'displayName': 'Content',
            'name': 'content',
            'type': 'string',
            'default': '',
        },
        {
            'displayName': 'Object Name',
            'name': 'object_name',
            'type': 'string',
            'default': '',
        },
    ]
    inputs = {
        "action": {
            "type": "dropdown",
            "default": "list_buckets",
            "options": ["list_buckets", "list_objects", "get_object", "upload_object", "delete_object"],
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
            creds = await self.get_credential("google_cloud_auth")
            access_token = creds.get("access_token")
            project_id = creds.get("project_id")
            
            if not access_token:
                return {"status": "error", "error": "Google Cloud Access Token required."}

            headers = {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json"
            }
            
            # 2. Connect to Real API
            base_url = "https://storage.googleapis.com/storage/v1"
            upload_url = "https://storage.googleapis.com/upload/storage/v1"
            action = self.get_config("action", "list_buckets")

            async with aiohttp.ClientSession() as session:
                if action == "list_buckets":
                    if not project_id:
                        return {"status": "error", "error": "project_id required"}
                    
                    url = f"{base_url}/b"
                    params = {"project": project_id}
                    async with session.get(url, headers=headers, params=params) as resp:
                        if resp.status != 200:
                            return {"status": "error", "error": f"GCS API Error: {resp.status}"}
                        res_data = await resp.json()
                        return {"status": "success", "data": {"result": res_data.get("items", [])}}

                elif action == "list_objects":
                    bucket = self.get_config("bucket_name")
                    if not bucket:
                        return {"status": "error", "error": "bucket_name required"}
                    
                    url = f"{base_url}/b/{bucket}/o"
                    async with session.get(url, headers=headers) as resp:
                        if resp.status != 200:
                            return {"status": "error", "error": f"GCS API Error: {resp.status}"}
                        res_data = await resp.json()
                        return {"status": "success", "data": {"result": res_data.get("items", [])}}

                elif action == "get_object":
                    bucket = self.get_config("bucket_name")
                    obj = self.get_config("object_name")
                    if not bucket or not obj:
                        return {"status": "error", "error": "bucket_name and object_name required"}
                    
                    url = f"{base_url}/b/{bucket}/o/{obj}"
                    params = {"alt": "media"}
                    async with session.get(url, headers=headers, params=params) as resp:
                        if resp.status != 200:
                            return {"status": "error", "error": f"GCS API Error: {resp.status}"}
                        content = await resp.text()
                        return {"status": "success", "data": {"result": content}}

                elif action == "upload_object":
                    bucket = self.get_config("bucket_name")
                    obj = self.get_config("object_name")
                    content = self.get_config("content") or str(input_data)
                    
                    if not bucket or not obj:
                        return {"status": "error", "error": "bucket_name and object_name required"}
                    
                    url = f"{upload_url}/b/{bucket}/o"
                    params = {"uploadType": "media", "name": obj}
                    headers["Content-Type"] = "text/plain"
                    async with session.post(url, headers=headers, params=params, data=content) as resp:
                        if resp.status != 200:
                            return {"status": "error", "error": f"GCS API Error: {resp.status}"}
                        res_data = await resp.json()
                        return {"status": "success", "data": {"result": res_data}}

                return {"status": "error", "error": f"Unsupported action: {action}"}

        except Exception as e:
            return {"status": "error", "error": f"GCS Node Failed: {str(e)}"}