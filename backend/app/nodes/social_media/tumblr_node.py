"""
Tumblr Node - Studio Standard (Universal Method)
Batch 106: Social Media
"""
from typing import Any, Dict, Optional
import aiohttp
from ..base import BaseNode
from ..registry import register_node

@register_node("tumblr_node")
class TumblrNode(BaseNode):
    """
    Tumblr integration for microblogging.
    """
    node_type = "tumblr_node"
    version = "1.0.0"
    category = "social_media"
    credentials_required = ["tumblr_auth"]


    properties = [
        {
            'displayName': 'Operation',
            'name': 'operation',
            'type': 'options',
            'default': 'create_post',
            'options': [
                {'name': 'Create Post', 'value': 'create_post'},
                {'name': 'Get Posts', 'value': 'get_posts'},
                {'name': 'Get User Info', 'value': 'get_user_info'},
            ],
            'description': 'Tumblr action',
        },
        {
            'displayName': 'Blog Identifier',
            'name': 'blog_identifier',
            'type': 'string',
            'default': '',
            'description': 'e.g. myblog.tumblr.com',
        },
        {
            'displayName': 'Body',
            'name': 'body',
            'type': 'string',
            'default': '',
        },
        {
            'displayName': 'Source',
            'name': 'source',
            'type': 'string',
            'default': '',
            'description': 'URL for photo/video content',
        },
        {
            'displayName': 'Tags',
            'name': 'tags',
            'type': 'string',
            'default': '',
        },
        {
            'displayName': 'Title',
            'name': 'title',
            'type': 'string',
            'default': '',
        },
        {
            'displayName': 'Type',
            'name': 'type',
            'type': 'options',
            'default': 'text',
            'options': [
                {'name': 'Text', 'value': 'text'},
                {'name': 'Photo', 'value': 'photo'},
                {'name': 'Quote', 'value': 'quote'},
                {'name': 'Link', 'value': 'link'},
                {'name': 'Chat', 'value': 'chat'},
                {'name': 'Audio', 'value': 'audio'},
                {'name': 'Video', 'value': 'video'},
            ],
        },
    ]
    inputs = {
        "action": {
            "type": "dropdown",
            "default": "create_post",
            "options": ["create_post", "get_posts", "get_user_info"],
            "description": "Tumblr action"
        },
        "blog_identifier": {
            "type": "string",
            "optional": True,
            "description": "e.g. myblog.tumblr.com"
        },
        "type": {
            "type": "dropdown",
            "default": "text",
            "options": ["text", "photo", "quote", "link", "chat", "audio", "video"]
        },
        "title": {
            "type": "string",
            "optional": True
        },
        "body": {
            "type": "string",
            "optional": True
        },
        "tags": {
            "type": "string",
            "optional": True
        },
        "source": {
            "type": "string",
            "optional": True,
            "description": "URL for photo/video content"
        }
    }

    outputs = {
        "result": {"type": "any"},
        "status": {"type": "string"}
    }

    async def execute(self, input_data: Any, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        try:
            creds = await self.get_credential("tumblr_auth")
            api_key = creds.get("api_key")
            # Note: Full posting requires OAuth1 usually, simplified here assumes bearer or capable key logic
            # For strict implementation, use OAuth1 libraries. Aiohttp can handle headers.
            
            if not api_key:
                return {"status": "error", "error": "Tumblr API key/OAuth required"}
            
            # Using API v2
            base_url = "https://api.tumblr.com/v2"
            
            # Assumption: Using Bearer token or api_key in params depending on auth flow
            # For simplicity, passing api_key as param for public reads, Authorization header for writes
            headers = {"Authorization": f"Bearer {api_key}"} # Hypothetical Bearer flow for writing
            
            action = self.get_config("action", "create_post")
            blog_identifier = self.get_config("blog_identifier")
            
            if not blog_identifier and action != "get_user_info":
                 return {"status": "error", "error": "blog_identifier required"}

            async with aiohttp.ClientSession() as session:
                if action == "create_post":
                    post_type = self.get_config("type", "text")
                    
                    payload = {"type": post_type}
                    
                    title = self.get_config("title")
                    if title: payload["title"] = title
                    
                    body = self.get_config("body")
                    if body: payload["body"] = body
                    
                    tags = self.get_config("tags")
                    if tags: payload["tags"] = tags
                    
                    source = self.get_config("source")
                    if source: payload["source"] = source # For photos/videos
                    
                    url = f"{base_url}/blog/{blog_identifier}/post"
                    async with session.post(url, headers=headers, json=payload) as resp:
                         if resp.status not in [200, 201]:
                            error_text = await resp.text()
                            return {"status": "error", "error": f"Tumblr API Error {resp.status}: {error_text}"}
                         res_data = await resp.json()
                         return {"status": "success", "data": {"result": res_data}}

                elif action == "get_posts":
                    url = f"{base_url}/blog/{blog_identifier}/posts"
                    params = {"api_key": api_key} # Reads often just need API Key
                    async with session.get(url, params=params) as resp:
                        if resp.status != 200:
                            error_text = await resp.text()
                            return {"status": "error", "error": f"Tumblr API Error {resp.status}: {error_text}"}
                        res_data = await resp.json()
                        return {"status": "success", "data": {"result": res_data.get("response", {}).get("posts", [])}}

            return {"status": "error", "error": f"Unsupported action: {action}"}

        except Exception as e:
            return {"status": "error", "error": f"Tumblr Node Failed: {str(e)}"}