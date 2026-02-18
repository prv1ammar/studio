"""
Ghost Node - Studio Standard
Batch 71: CMS & Web Engines
"""
from typing import Any, Dict, Optional, List
import aiohttp
from ..base import BaseNode
from ..registry import register_node

@register_node("ghost_node")
class GhostNode(BaseNode):
    """
    Automate publishing and content management via the Ghost Admin API.
    """
    node_type = "ghost_node"
    version = "1.0.0"
    category = "cms"
    credentials_required = ["ghost_auth"]


    properties = [
        {
            'displayName': 'Operation',
            'name': 'operation',
            'type': 'options',
            'default': 'list_posts',
            'options': [
                {'name': 'List Posts', 'value': 'list_posts'},
                {'name': 'Get Post', 'value': 'get_post'},
                {'name': 'Create Post', 'value': 'create_post'},
                {'name': 'List Pages', 'value': 'list_pages'},
            ],
            'description': 'Ghost action',
        },
        {
            'displayName': 'Post Id',
            'name': 'post_id',
            'type': 'string',
            'default': '',
        },
        {
            'displayName': 'Url',
            'name': 'url',
            'type': 'string',
            'default': '',
            'description': 'Base URL of your Ghost site (e.g. https://your-site.ghost.io)',
            'required': True,
        },
    ]
    inputs = {
        "action": {
            "type": "dropdown",
            "default": "list_posts",
            "options": ["list_posts", "get_post", "create_post", "list_pages"],
            "description": "Ghost action"
        },
        "url": {
            "type": "string",
            "required": True,
            "description": "Base URL of your Ghost site (e.g. https://your-site.ghost.io)"
        },
        "post_id": {
            "type": "string",
            "optional": True
        }
    }

    outputs = {
        "result": {"type": "any"},
        "status": {"type": "string"},
        "count": {"type": "number"}
    }

    async def execute(self, input_data: Any, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        try:
            creds = await self.get_credential("ghost_auth")
            # Note: Ghost Admin API usually requires a JWT. 
            # For simplicity in this node, we assume the user provides a pre-generated token or the node logic handles it.
            token = creds.get("token") if creds else self.get_config("token")
            
            if not token:
                return {"status": "error", "error": "Ghost Admin Token is required."}

            headers = {
                "Authorization": f"Ghost {token}",
                "Content-Type": "application/json"
            }
            
            base_url = self.get_config("url").rstrip("/")
            api_url = f"{base_url}/ghost/api/admin"
            action = self.get_config("action", "list_posts")

            async with aiohttp.ClientSession() as session:
                if action == "list_posts":
                    async with session.get(f"{api_url}/posts/", headers=headers) as resp:
                        res_data = await resp.json()
                        posts = res_data.get("posts", [])
                        return {"status": "success", "data": {"result": posts, "count": len(posts)}}

                elif action == "get_post":
                    p_id = self.get_config("post_id") or str(input_data)
                    async with session.get(f"{api_url}/posts/{p_id}/", headers=headers) as resp:
                        res_data = await resp.json()
                        return {"status": "success", "data": {"result": res_data.get("posts", [{}])[0]}}

                elif action == "list_pages":
                    async with session.get(f"{api_url}/pages/", headers=headers) as resp:
                        res_data = await resp.json()
                        pages = res_data.get("pages", [])
                        return {"status": "success", "data": {"result": pages, "count": len(pages)}}

                elif action == "create_post":
                    title = str(input_data)
                    payload = {
                        "posts": [{
                            "title": title,
                            "status": "draft"
                        }]
                    }
                    async with session.post(f"{api_url}/posts/", headers=headers, json=payload) as resp:
                        res_data = await resp.json()
                        return {"status": "success", "data": {"result": res_data.get("posts", [{}])[0], "status": "created"}}

                return {"status": "error", "error": f"Unsupported action: {action}"}

        except Exception as e:
            return {"status": "error", "error": f"Ghost Node Failed: {str(e)}"}