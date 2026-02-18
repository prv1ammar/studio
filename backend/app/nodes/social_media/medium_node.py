"""
Medium Node - Studio Standard (Universal Method)
Batch 106: Social Media
"""
from typing import Any, Dict, Optional, List
import aiohttp
from ..base import BaseNode
from ..registry import register_node

@register_node("medium_node")
class MediumNode(BaseNode):
    """
    Medium integration for publishing articles.
    """
    node_type = "medium_node"
    version = "1.0.0"
    category = "social_media"
    credentials_required = ["medium_auth"]


    properties = [
        {
            'displayName': 'Operation',
            'name': 'operation',
            'type': 'options',
            'default': 'create_post',
            'options': [
                {'name': 'Create Post', 'value': 'create_post'},
                {'name': 'Get User', 'value': 'get_user'},
                {'name': 'List Publications', 'value': 'list_publications'},
            ],
            'description': 'Medium action',
        },
        {
            'displayName': 'Author Id',
            'name': 'author_id',
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
            'displayName': 'Content Format',
            'name': 'content_format',
            'type': 'options',
            'default': 'html',
            'options': [
                {'name': 'Html', 'value': 'html'},
                {'name': 'Markdown', 'value': 'markdown'},
            ],
        },
        {
            'displayName': 'Publication Id',
            'name': 'publication_id',
            'type': 'string',
            'default': '',
        },
        {
            'displayName': 'Publish Status',
            'name': 'publish_status',
            'type': 'options',
            'default': 'public',
            'options': [
                {'name': 'Public', 'value': 'public'},
                {'name': 'Draft', 'value': 'draft'},
                {'name': 'Unlisted', 'value': 'unlisted'},
            ],
        },
        {
            'displayName': 'Tags',
            'name': 'tags',
            'type': 'string',
            'default': '',
            'description': 'Comma separated tags',
        },
        {
            'displayName': 'Title',
            'name': 'title',
            'type': 'string',
            'default': '',
        },
    ]
    inputs = {
        "action": {
            "type": "dropdown",
            "default": "create_post",
            "options": ["create_post", "get_user", "list_publications"],
            "description": "Medium action"
        },
        "author_id": {
            "type": "string",
            "optional": True
        },
        "title": {
            "type": "string",
            "optional": True
        },
        "content_format": {
            "type": "dropdown",
            "default": "html",
            "options": ["html", "markdown"]
        },
        "content": {
            "type": "string",
            "optional": True
        },
        "tags": {
            "type": "string",
            "optional": True,
            "description": "Comma separated tags"
        },
        "publish_status": {
            "type": "dropdown",
            "default": "public",
            "options": ["public", "draft", "unlisted"]
        },
        "publication_id": {
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
            creds = await self.get_credential("medium_auth")
            access_token = creds.get("access_token")
            
            if not access_token:
                return {"status": "error", "error": "Medium access token required"}

            base_url = "https://api.medium.com/v1"
            headers = {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json"
            }
            
            action = self.get_config("action", "create_post")

            async with aiohttp.ClientSession() as session:
                if action == "get_user":
                    url = f"{base_url}/me"
                    async with session.get(url, headers=headers) as resp:
                         if resp.status != 200:
                            error_text = await resp.text()
                            return {"status": "error", "error": f"Medium API Error {resp.status}: {error_text}"}
                         res_data = await resp.json()
                         return {"status": "success", "data": {"result": res_data.get("data")}}

                elif action == "create_post":
                    author_id = self.get_config("author_id")
                    title = self.get_config("title")
                    content_format = self.get_config("content_format", "html")
                    content = self.get_config("content")
                    tags = self.get_config("tags", "")
                    status = self.get_config("publish_status", "public")
                    publication_id = self.get_config("publication_id")
                    
                    if not title or not content:
                        return {"status": "error", "error": "title and content required"}
                        
                    if not author_id:
                        # Fetch user ID if not provided
                        user_resp = await session.get(f"{base_url}/me", headers=headers)
                        user_data = await user_resp.json()
                        author_id = user_data.get("data", {}).get("id")
                        if not author_id:
                             return {"status": "error", "error": "Could not determine author_id from token"}
                    
                    payload = {
                        "title": title,
                        "contentFormat": content_format,
                        "content": content,
                        "publishStatus": status
                    }
                    if tags:
                        payload["tags"] = [tag.strip() for tag in tags.split(",") if tag.strip()]
                        
                    # Target URL depends on if publishing to user or publication
                    if publication_id:
                        url = f"{base_url}/publications/{publication_id}/posts"
                    else:
                        url = f"{base_url}/users/{author_id}/posts"
                        
                    async with session.post(url, headers=headers, json=payload) as resp:
                        if resp.status not in [200, 201]:
                            error_text = await resp.text()
                            return {"status": "error", "error": f"Medium API Error {resp.status}: {error_text}"}
                        res_data = await resp.json()
                        return {"status": "success", "data": {"result": res_data.get("data")}}

            return {"status": "error", "error": f"Unsupported action: {action}"}

        except Exception as e:
            return {"status": "error", "error": f"Medium Node Failed: {str(e)}"}