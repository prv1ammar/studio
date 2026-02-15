"""
Sync.com Node - Studio Standard (Universal Method)
Batch 107: Cloud Storage
"""
from typing import Any, Dict, Optional
import aiohttp
from ...base import BaseNode
from ...registry import register_node

# Sync.com does not offer a public API (officially) for third-party automation in the same way.
# However, for parity we can implement a placeholder or use the 'Email to Sync' feature logic if applicable.
# OR, use a webdav interface if they support it (some plans do).
# Since reliable API is missing, we will implement a "Placeholder" explaining this limitation
# or implement a basic WebDAV client if we assume WebDAV access.
# Choice: Implement a basic WebDAV wrapper structure, as Sync.com supports WebDAV on some business plans.

@register_node("sync_com_node")
class SyncComNode(BaseNode):
    """
    Sync.com integration via WebDAV (Business Plans).
    """
    node_type = "sync_com_node"
    version = "1.0.0"
    category = "storage"
    credentials_required = ["sync_com_webdav_auth"]

    inputs = {
        "action": {
            "type": "dropdown",
            "default": "list_folder",
            "options": ["list_folder", "upload_file"],
            "description": "WebDAV action"
        },
        "path": {
            "type": "string",
            "default": "/",
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
            creds = await self.get_credential("sync_com_webdav_auth")
            username = creds.get("username")
            password = creds.get("password")
            webdav_url = creds.get("webdav_url", "https://webdav.sync.com") 
            
            if not username or not password:
                return {"status": "error", "error": "Sync.com WebDAV credentials required"}

            auth = aiohttp.BasicAuth(username, password)
            action = self.get_config("action", "list_folder")
            path = self.get_config("path", "/").lstrip("/")

            async with aiohttp.ClientSession() as session:
                url = f"{webdav_url}/{path}"
                
                if action == "list_folder":
                    # PROPFIND method usually required for WebDAV
                    # aiohttp request method allows custom verbs
                    headers = {"Depth": "1"}
                    async with session.request("PROPFIND", url, auth=auth, headers=headers) as resp:
                         if resp.status not in [200, 207]:
                            error_text = await resp.text()
                            return {"status": "error", "error": f"WebDAV Error {resp.status}: {error_text}"}
                         # XML parsing needed effectively
                         return {"status": "success", "data": {"result": await resp.text()}}

                elif action == "upload_file":
                    file_content = self.get_config("file_content")
                    if file_content is None:
                        return {"status": "error", "error": "file_content required"}
                    
                    async with session.put(url, data=file_content, auth=auth) as resp:
                        if resp.status not in [200, 201, 204]:
                            error_text = await resp.text()
                            return {"status": "error", "error": f"WebDAV Upload Error {resp.status}: {error_text}"}
                        return {"status": "success", "data": {"result": "File uploaded"}}

            return {"status": "error", "error": f"Unsupported action: {action}"}

        except Exception as e:
            return {"status": "error", "error": f"Sync.com Node Failed: {str(e)}"}
