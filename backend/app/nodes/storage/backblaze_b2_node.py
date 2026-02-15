"""
Backblaze B2 Node - Studio Standard (Universal Method)
Batch 107: Cloud Storage
"""
from typing import Any, Dict, Optional
import aiohttp
from ...base import BaseNode
from ...registry import register_node

@register_node("backblaze_b2_node")
class BackblazeB2Node(BaseNode):
    """
    Backblaze B2 cloud storage integration.
    """
    node_type = "backblaze_b2_node"
    version = "1.0.0"
    category = "storage"
    credentials_required = ["backblaze_b2_auth"]

    inputs = {
        "action": {
            "type": "dropdown",
            "default": "upload_file",
            "options": ["upload_file", "list_buckets", "download_file"],
            "description": "B2 action"
        },
        "bucket_id": {
            "type": "string",
            "optional": True
        },
        "file_name": {
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
            creds = await self.get_credential("backblaze_b2_auth")
            account_id = creds.get("application_key_id")
            application_key = creds.get("application_key")
            
            if not account_id or not application_key:
                return {"status": "error", "error": "Backblaze B2 credentials required"}

            action = self.get_config("action", "upload_file")

            async with aiohttp.ClientSession() as session:
                # 1. Authorize Account
                auth_url = "https://api.backblazeb2.com/b2api/v2/b2_authorize_account"
                auth = aiohttp.BasicAuth(account_id, application_key)
                
                async with session.get(auth_url, auth=auth) as resp:
                     if resp.status != 200:
                         error_text = await resp.text()
                         return {"status": "error", "error": f"B2 Auth Error {resp.status}: {error_text}"}
                     auth_data = await resp.json()
                     
                     api_url = auth_data["apiUrl"]
                     auth_token = auth_data["authorizationToken"]
                     download_url = auth_data["downloadUrl"]
                
                # 2. Perform Action
                if action == "list_buckets":
                    account_id_from_auth = auth_data["accountId"]
                    payload = {"accountId": account_id_from_auth}
                    headers = {"Authorization": auth_token}
                    
                    async with session.post(f"{api_url}/b2api/v2/b2_list_buckets", headers=headers, json=payload) as resp:
                         if resp.status != 200:
                             error_text = await resp.text()
                             return {"status": "error", "error": f"B2 API Error {resp.status}: {error_text}"}
                         res_data = await resp.json()
                         return {"status": "success", "data": {"result": res_data.get("buckets", [])}}
                
                elif action == "upload_file":
                   bucket_id = self.get_config("bucket_id")
                   file_name = self.get_config("file_name")
                   file_content = self.get_config("file_content")
                   
                   if not bucket_id or not file_name or file_content is None:
                        return {"status": "error", "error": "bucket_id, file_name, and file_content required"}
                   
                   # Get Upload URL
                   headers = {"Authorization": auth_token}
                   payload = {"bucketId": bucket_id}
                   
                   async with session.post(f"{api_url}/b2api/v2/b2_get_upload_url", headers=headers, json=payload) as resp:
                        if resp.status != 200:
                            error_text = await resp.text()
                            return {"status": "error", "error": f"B2 API Error (get upload url) {resp.status}: {error_text}"}
                        upload_data = await resp.json()
                        upload_url = upload_data["uploadUrl"]
                        upload_token = upload_data["authorizationToken"]
                   
                   # Upload File
                   import hashlib
                   sha1_content = hashlib.sha1(file_content.encode('utf-8')).hexdigest()
                   
                   upload_headers = {
                       "Authorization": upload_token,
                       "X-Bz-File-Name": file_name, # URL encoded ideally
                       "Content-Type": "text/plain", # Can be specific
                       "X-Bz-Content-Sha1": sha1_content
                   }
                   
                   async with session.post(upload_url, headers=upload_headers, data=file_content) as resp:
                       if resp.status != 200:
                           error_text = await resp.text()
                           return {"status": "error", "error": f"B2 API Error (upload) {resp.status}: {error_text}"}
                       res_data = await resp.json()
                       return {"status": "success", "data": {"result": res_data}}

            return {"status": "error", "error": f"Unsupported action: {action}"}

        except Exception as e:
            return {"status": "error", "error": f"B2 Node Failed: {str(e)}"}
