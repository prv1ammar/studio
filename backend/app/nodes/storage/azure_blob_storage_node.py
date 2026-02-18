"""
Azure Blob Storage Node - Studio Standard (Universal Method)
Batch 107: Cloud Storage
"""
from typing import Any, Dict, Optional
import aiohttp
from ..base import BaseNode
from ..registry import register_node

@register_node("azure_blob_storage_node")
class AzureBlobStorageNode(BaseNode):
    """
    Azure Blob Storage integration.
    """
    node_type = "azure_blob_storage_node"
    version = "1.0.0"
    category = "storage"
    credentials_required = ["azure_storage_auth"]


    properties = [
        {
            'displayName': 'Operation',
            'name': 'operation',
            'type': 'options',
            'default': 'upload_blob',
            'options': [
                {'name': 'Upload Blob', 'value': 'upload_blob'},
                {'name': 'List Containers', 'value': 'list_containers'},
                {'name': 'Download Blob', 'value': 'download_blob'},
            ],
            'description': 'Azure Blob action',
        },
        {
            'displayName': 'Blob Name',
            'name': 'blob_name',
            'type': 'string',
            'default': '',
        },
        {
            'displayName': 'Container Name',
            'name': 'container_name',
            'type': 'string',
            'default': '',
        },
        {
            'displayName': 'File Content',
            'name': 'file_content',
            'type': 'string',
            'default': '',
        },
    ]
    inputs = {
        "action": {
            "type": "dropdown",
            "default": "upload_blob",
            "options": ["upload_blob", "list_containers", "download_blob"],
            "description": "Azure Blob action"
        },
        "container_name": {
            "type": "string",
            "optional": True
        },
        "blob_name": {
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
            creds = await self.get_credential("azure_storage_auth")
            account_name = creds.get("account_name")
            account_key = creds.get("account_key")
            sas_token = creds.get("sas_token") 
            # Note: Production uses SharedKey auth (hmac) or SAS. Simplified here assumes SAS for REST

            if not account_name or not sas_token:
                return {"status": "error", "error": "Azure storage account name and SAS token required"}

            base_url = f"https://{account_name}.blob.core.windows.net"
            
            action = self.get_config("action", "upload_blob")

            async with aiohttp.ClientSession() as session:
                if action == "upload_blob":
                    container = self.get_config("container_name")
                    blob = self.get_config("blob_name")
                    content = self.get_config("file_content")
                    
                    if not container or not blob or content is None:
                        return {"status": "error", "error": "container_name, blob_name, and file_content required"}
                    
                    url = f"{base_url}/{container}/{blob}?{sas_token}"
                    headers = {
                        "x-ms-blob-type": "BlockBlob",
                        "Content-Type": "text/plain" # Or appropriate
                    }
                    
                    async with session.put(url, headers=headers, data=content) as resp:
                         if resp.status != 201:
                            error_text = await resp.text()
                            return {"status": "error", "error": f"Azure API Error {resp.status}: {error_text}"}
                         return {"status": "success", "data": {"result": {"message": "Blob uploaded"}}}

                elif action == "list_containers":
                    url = f"{base_url}/?comp=list&{sas_token}"
                    async with session.get(url) as resp:
                        if resp.status != 200:
                            error_text = await resp.text()
                            return {"status": "error", "error": f"Azure API Error {resp.status}: {error_text}"}
                        # XML Parsing would be needed here for full data, returning raw text for now
                        res_text = await resp.text()
                        return {"status": "success", "data": {"result": {"xml_response": res_text}}}

            return {"status": "error", "error": f"Unsupported action: {action}"}

        except Exception as e:
            return {"status": "error", "error": f"Azure Node Failed: {str(e)}"}