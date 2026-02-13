"""
OneDrive Node - Studio Standard (Universal Method)
Batch 94: Cloud Storage (n8n Critical)
"""
from typing import Any, Dict, Optional, List
import aiohttp
from ...base import BaseNode
from ...registry import register_node

@register_node("onedrive_node")
class OneDriveNode(BaseNode):
    """
    Manage files in OneDrive personal via Microsoft Graph API.
    """
    node_type = "onedrive_node"
    version = "1.0.0"
    category = "storage"
    credentials_required = ["microsoft_auth"]

    inputs = {
        "action": {
            "type": "dropdown",
            "default": "list_children",
            "options": ["list_children", "get_metadata", "download_file", "upload_file", "create_folder"],
            "description": "OneDrive action"
        },
        "item_path": {
            "type": "string",
            "default": "/",
            "description": "Path to item (e.g. /Documents/file.txt)"
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
            creds = await self.get_credential("microsoft_auth")
            access_token = creds.get("access_token")
            
            if not access_token:
                return {"status": "error", "error": "Microsoft Access Token required."}

            headers = {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json"
            }
            
            # 2. Connect to Real API
            base_url = "https://graph.microsoft.com/v1.0/me/drive/root"
            action = self.get_config("action", "list_children")

            async with aiohttp.ClientSession() as session:
                if action == "list_children":
                    path = self.get_config("item_path", "/")
                    if path == "/":
                        url = f"{base_url}/children"
                    else:
                        url = f"{base_url}:{path}:/children"
                    
                    async with session.get(url, headers=headers) as resp:
                        if resp.status != 200:
                            return {"status": "error", "error": f"OneDrive API Error: {resp.status}"}
                        res_data = await resp.json()
                        return {"status": "success", "data": {"result": res_data.get("value", [])}}

                elif action == "get_metadata":
                    path = self.get_config("item_path")
                    if not path:
                          return {"status": "error", "error": "item_path required"}
                          
                    url = f"{base_url}:{path}"
                    async with session.get(url, headers=headers) as resp:
                        if resp.status != 200:
                            return {"status": "error", "error": f"OneDrive API Error: {resp.status}"}
                        res_data = await resp.json()
                        return {"status": "success", "data": {"result": res_data}}

                elif action == "upload_file":
                    # Simple upload for small files
                    path = self.get_config("item_path")
                    content = self.get_config("content") or str(input_data)
                    
                    if not path:
                        return {"status": "error", "error": "item_path required"}
                    
                    url = f"{base_url}:{path}:/content"
                    headers["Content-Type"] = "text/plain"  # Assume text for now
                    async with session.put(url, headers=headers, data=content) as resp:
                        if resp.status not in [200, 201]:
                            return {"status": "error", "error": f"OneDrive API Error: {resp.status}"}
                        res_data = await resp.json()
                        return {"status": "success", "data": {"result": res_data}}

                elif action == "create_folder":
                    # For creating folder, we need the parent path
                    path = self.get_config("item_path")
                    if not path:
                        return {"status": "error", "error": "item_path required (e.g. /NewFolder)"}
                    
                    # Assume creating in root for simplicity if no parent specified logic
                    # This is naive implementation
                    url = f"{base_url}/children"
                    payload = {
                        "name": path.strip("/"),
                        "folder": {},
                        "@microsoft.graph.conflictBehavior": "rename"
                    }
                    async with session.post(url, headers=headers, json=payload) as resp:
                        if resp.status != 201:
                             return {"status": "error", "error": f"OneDrive API Error: {resp.status}"}
                        res_data = await resp.json()
                        return {"status": "success", "data": {"result": res_data}}

                return {"status": "error", "error": f"Unsupported action: {action}"}

        except Exception as e:
            return {"status": "error", "error": f"OneDrive Node Failed: {str(e)}"}
