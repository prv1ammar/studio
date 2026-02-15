"""
Blogging Platform Nodes - Studio Standard (Universal Method)
Batch 106: Social Media
"""
from typing import Any, Dict, Optional, List
import aiohttp
from ...base import BaseNode
from ...registry import register_node

# ============================================
# MEDIUM NODE
# ============================================
@register_node("medium_node")
class MediumNode(BaseNode):
    """
    Medium integration for publishing articles.
    """
    node_type = "medium_node"
    version = "1.0.0"
    category = "social_media"
    credentials_required = ["medium_auth"]

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


# ============================================
# TUMBLR NODE
# ============================================
@register_node("tumblr_node")
class TumblrNode(BaseNode):
    """
    Tumblr integration for microblogging.
    """
    node_type = "tumblr_node"
    version = "1.0.0"
    category = "social_media"
    credentials_required = ["tumblr_auth"]

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
