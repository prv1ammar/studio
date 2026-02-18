import aiohttp
from typing import Any, Dict, Optional, List
from ..base import BaseNode
from ..registry import register_node
import base64
import json

@register_node("wordpress_action")
class WordPressNode(BaseNode):
    """
    Automate WordPress actions (Posts).
    """
    node_type = "wordpress_action"
    version = "1.0.0"
    category = "integrations"
    credentials_required = ["wordpress_auth"]


    properties = [
        {
            'displayName': 'Operation',
            'name': 'operation',
            'type': 'string',
            'default': 'create_post',
        },
        {
            'displayName': 'Content',
            'name': 'content',
            'type': 'string',
            'default': '',
        },
        {
            'displayName': 'Post Status',
            'name': 'post_status',
            'type': 'string',
            'default': 'publish',
        },
        {
            'displayName': 'Title',
            'name': 'title',
            'type': 'string',
            'default': '',
        },
    ]
    inputs = {
        "action": {"type": "string", "default": "create_post", "enum": ["create_post", "list_posts"]},
        "title": {"type": "string", "optional": True},
        "content": {"type": "string", "optional": True},
        "post_status": {"type": "string", "default": "publish"}
    }
    outputs = {
        "results": {"type": "array"},
        "post_id": {"type": "string"},
        "link": {"type": "string"},
        "status": {"type": "string"}
    }

    async def execute(self, input_data: Any, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        try:
            # 1. Resolve Auth
            creds = await self.get_credential("wordpress_auth")
            base_url = creds.get("base_url") if creds else self.get_config("base_url")
            username = creds.get("username") if creds else self.get_config("username")
            app_password = creds.get("app_password") if creds else self.get_config("app_password")

            if not all([base_url, username, app_password]):
                return {"status": "error", "error": "WordPress URL, Username, and App Password are required."}

            base_url = base_url.rstrip('/')
            auth_string = f"{username}:{app_password}"
            auth_encoded = base64.b64encode(auth_string.encode()).decode()
            headers = {
                "Authorization": f"Basic {auth_encoded}",
                "Content-Type": "application/json"
            }

            action = self.get_config("action", "create_post")

            async with aiohttp.ClientSession() as session:
                if action == "create_post":
                    payload = {
                        "title": self.get_config("title", "Studio Post"),
                        "content": str(input_data) if isinstance(input_data, str) else self.get_config("content", ""),
                        "status": self.get_config("post_status", "publish")
                    }
                    if isinstance(input_data, dict):
                        payload["title"] = input_data.get("title") or payload["title"]
                        payload["content"] = input_data.get("content") or payload["content"]

                    url = f"{base_url}/wp-json/wp/v2/posts"
                    async with session.post(url, json=payload, headers=headers) as resp:
                        result = await resp.json()
                        if resp.status >= 400:
                            return {"status": "error", "error": f"WP Error: {result.get('message')}"}
                        return {
                            "status": "success",
                            "data": {
                                "post_id": result.get("id"),
                                "link": result.get("link")
                            }
                        }

                elif action == "list_posts":
                    url = f"{base_url}/wp-json/wp/v2/posts"
                    async with session.get(url, headers=headers) as resp:
                        result = await resp.json()
                        if resp.status >= 400:
                            return {"status": "error", "error": f"WP Error: {result.get('message')}"}
                        
                        posts = [{"id": p["id"], "title": p["title"]["rendered"], "link": p["link"]} for p in result]
                        return {
                            "status": "success",
                            "data": {
                                "results": posts,
                                "count": len(posts)
                            }
                        }

            return {"status": "error", "error": f"Unsupported WordPress action: {action}"}

        except Exception as e:
            return {"status": "error", "error": f"WordPress Node Error: {str(e)}"}