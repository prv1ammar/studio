"""
GitBook Node - Studio Standard
Batch 60: Knowledge Management
"""
from typing import Any, Dict, Optional, List
import aiohttp
from ...base import BaseNode
from ...registry import register_node

@register_node("gitbook_node")
class GitBookNode(BaseNode):
    """
    Automate GitBook knowledge management.
    Supports listing spaces, retrieving content, and searching.
    """
    node_type = "gitbook_node"
    version = "1.0.0"
    category = "knowledge"
    credentials_required = ["gitbook_auth"]

    inputs = {
        "action": {
            "type": "dropdown",
            "default": "list_spaces",
            "options": ["list_spaces", "get_space", "list_pages", "search", "get_page_content"],
            "description": "GitBook action"
        },
        "space_id": {
            "type": "string",
            "optional": True,
            "description": "Unique ID of the GitBook space"
        },
        "page_id": {
            "type": "string",
            "optional": True,
            "description": "Unique ID of the page"
        },
        "query": {
            "type": "string",
            "optional": True,
            "description": "Search query"
        }
    }

    outputs = {
        "result": {"type": "any"},
        "status": {"type": "string"},
        "count": {"type": "number"}
    }

    async def execute(self, input_data: Any, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        try:
            # 1. Resolve Auth
            creds = await self.get_credential("gitbook_auth")
            api_token = creds.get("api_token") if creds else self.get_config("api_token")
            
            if not api_token:
                return {"status": "error", "error": "GitBook API Token is required."}

            headers = {
                "Authorization": f"Bearer {api_token}",
                "Content-Type": "application/json"
            }
            
            base_url = "https://api.gitbook.com/v1"
            action = self.get_config("action", "list_spaces")
            space_id = self.get_config("space_id")
            
            async with aiohttp.ClientSession() as session:
                if action == "list_spaces":
                    url = f"{base_url}/orgs" # Or user spaces? Let's check orgs first or list root spaces
                    # For users, it's often better to check spaces directly
                    url = f"{base_url}/spaces"
                    async with session.get(url, headers=headers) as resp:
                        res_data = await resp.json()
                        items = res_data.get("items", [])
                        return {"status": "success", "data": {"result": items, "count": len(items)}}

                elif action == "get_space":
                    if not space_id:
                         return {"status": "error", "error": "Space ID is required."}
                    url = f"{base_url}/spaces/{space_id}"
                    async with session.get(url, headers=headers) as resp:
                        res_data = await resp.json()
                        return {"status": "success", "data": {"result": res_data}}

                elif action == "list_pages":
                    if not space_id:
                         return {"status": "error", "error": "Space ID is required."}
                    # Pages are found within a content object
                    url = f"{base_url}/spaces/{space_id}/content/v/latest"
                    async with session.get(url, headers=headers) as resp:
                        res_data = await resp.json()
                        # GitBook nests pages in a tree
                        pages = res_data.get("pages", [])
                        return {"status": "success", "data": {"result": pages, "count": len(pages)}}

                elif action == "search":
                    query = self.get_config("query") or (str(input_data) if input_data else "")
                    url = f"{base_url}/search"
                    params = {"query": query}
                    async with session.get(url, headers=headers, params=params) as resp:
                        res_data = await resp.json()
                        items = res_data.get("items", [])
                        return {"status": "success", "data": {"result": items, "count": len(items)}}

                return {"status": "error", "error": f"Unsupported GitBook action: {action}"}

        except Exception as e:
            return {"status": "error", "error": f"GitBook Node Failed: {str(e)}"}
