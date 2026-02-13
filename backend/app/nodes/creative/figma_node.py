"""
Figma Node - Studio Standard
Batch 78: Design & Creative
"""
from typing import Any, Dict, Optional, List
import aiohttp
from ...base import BaseNode
from ...registry import register_node

@register_node("figma_node")
class FigmaNode(BaseNode):
    """
    Access Figma files, comments, and project versions via the Figma REST API.
    """
    node_type = "figma_node"
    version = "1.0.0"
    category = "creative"
    credentials_required = ["figma_auth"]

    inputs = {
        "action": {
            "type": "dropdown",
            "default": "get_file",
            "options": ["get_file", "get_file_nodes", "get_comments", "post_comment", "get_versions"],
            "description": "Figma action"
        },
        "file_key": {
            "type": "string",
            "required": True,
            "description": "Unique key for the Figma file"
        },
        "message": {
            "type": "string",
            "optional": True,
            "description": "Comment message for post_comment"
        }
    }

    outputs = {
        "result": {"type": "any"},
        "status": {"type": "string"}
    }

    async def execute(self, input_data: Any, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        try:
            creds = await self.get_credential("figma_auth")
            access_token = creds.get("access_token") if creds else self.get_config("access_token")
            
            if not access_token:
                return {"status": "error", "error": "Figma Personal Access Token is required."}

            headers = {
                "X-Figma-Token": access_token if not access_token.startswith("Bearer ") else access_token.replace("Bearer ", ""),
                "Accept": "application/json"
            }
            
            base_url = "https://api.figma.com/v1"
            action = self.get_config("action", "get_file")
            file_key = self.get_config("file_key") or str(input_data)

            async with aiohttp.ClientSession() as session:
                if action == "get_file":
                    url = f"{base_url}/files/{file_key}"
                    async with session.get(url, headers=headers) as resp:
                        res_data = await resp.json()
                        return {"status": "success", "data": {"result": res_data}}

                elif action == "get_comments":
                    url = f"{base_url}/files/{file_key}/comments"
                    async with session.get(url, headers=headers) as resp:
                        res_data = await resp.json()
                        return {"status": "success", "data": {"result": res_data.get("comments", [])}}

                elif action == "post_comment":
                    url = f"{base_url}/files/{file_key}/comments"
                    payload = {"message": self.get_config("message") or str(input_data)}
                    async with session.post(url, headers=headers, json=payload) as resp:
                        res_data = await resp.json()
                        return {"status": "success", "data": {"result": res_data}}

                elif action == "get_versions":
                    url = f"{base_url}/files/{file_key}/versions"
                    async with session.get(url, headers=headers) as resp:
                        res_data = await resp.json()
                        return {"status": "success", "data": {"result": res_data.get("versions", [])}}

                return {"status": "error", "error": f"Unsupported action: {action}"}

        except Exception as e:
            return {"status": "error", "error": f"Figma Node Failed: {str(e)}"}
