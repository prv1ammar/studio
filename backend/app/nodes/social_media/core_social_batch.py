"""
Core Social Media Nodes - Studio Standard (Universal Method)
Batch 106: Social Media
"""
from typing import Any, Dict, Optional, List
import aiohttp
from ..base import BaseNode
from ..registry import register_node

# ============================================
# FACEBOOK PAGES NODE
# ============================================
@register_node("facebook_pages_node")
class FacebookPagesNode(BaseNode):
    """
    Facebook Pages integration for publishing and management.
    """
    node_type = "facebook_pages_node"
    version = "1.0.0"
    category = "social_media"
    credentials_required = ["facebook_graph_auth"]


    properties = [
        {
            'displayName': 'Operation',
            'name': 'operation',
            'type': 'options',
            'default': 'create_post',
            'options': [
                {'name': 'Create Post', 'value': 'create_post'},
                {'name': 'Get Posts', 'value': 'get_posts'},
                {'name': 'Get Page Info', 'value': 'get_page_info'},
                {'name': 'Upload Photo', 'value': 'upload_photo'},
            ],
            'description': 'Facebook action',
        },
        {
            'displayName': 'Link',
            'name': 'link',
            'type': 'string',
            'default': '',
        },
        {
            'displayName': 'Message',
            'name': 'message',
            'type': 'string',
            'default': '',
        },
        {
            'displayName': 'Page Id',
            'name': 'page_id',
            'type': 'string',
            'default': '',
        },
        {
            'displayName': 'Photo Url',
            'name': 'photo_url',
            'type': 'string',
            'default': '',
        },
    ]
    inputs = {
        "action": {
            "type": "dropdown",
            "default": "create_post",
            "options": ["create_post", "get_posts", "get_page_info", "upload_photo"],
            "description": "Facebook action"
        },
        "page_id": {
            "type": "string",
            "optional": True
        },
        "message": {
            "type": "string",
            "optional": True
        },
        "link": {
            "type": "string",
            "optional": True
        },
        "photo_url": {
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
            creds = await self.get_credential("facebook_graph_auth")
            access_token = creds.get("page_access_token") or creds.get("access_token")
            
            if not access_token:
                return {"status": "error", "error": "Facebook Page access token required"}

            base_url = "https://graph.facebook.com/v19.0"
            
            action = self.get_config("action", "create_post")
            page_id = self.get_config("page_id", "me")

            async with aiohttp.ClientSession() as session:
                if action == "create_post":
                    message = self.get_config("message")
                    link = self.get_config("link")
                    
                    if not message:
                        return {"status": "error", "error": "message required"}
                    
                    url = f"{base_url}/{page_id}/feed"
                    payload = {"message": message, "access_token": access_token}
                    if link:
                        payload["link"] = link
                    
                    async with session.post(url, json=payload) as resp:
                        if resp.status != 200:
                            error_text = await resp.text()
                            return {"status": "error", "error": f"Facebook API Error {resp.status}: {error_text}"}
                        res_data = await resp.json()
                        return {"status": "success", "data": {"result": res_data}}

                elif action == "upload_photo":
                    photo_url = self.get_config("photo_url")
                    message = self.get_config("message")
                    
                    if not photo_url:
                        return {"status": "error", "error": "photo_url required"}
                    
                    url = f"{base_url}/{page_id}/photos"
                    payload = {
                        "url": photo_url, 
                        "access_token": access_token
                    }
                    if message:
                        payload["message"] = message
                        
                    async with session.post(url, json=payload) as resp:
                         if resp.status != 200:
                            error_text = await resp.text()
                            return {"status": "error", "error": f"Facebook API Error {resp.status}: {error_text}"}
                         res_data = await resp.json()
                         return {"status": "success", "data": {"result": res_data}}

                elif action == "get_posts":
                    url = f"{base_url}/{page_id}/feed"
                    params = {"access_token": access_token}
                    async with session.get(url, params=params) as resp:
                        if resp.status != 200:
                            error_text = await resp.text()
                            return {"status": "error", "error": f"Facebook API Error {resp.status}: {error_text}"}
                        res_data = await resp.json()
                        return {"status": "success", "data": {"result": res_data.get("data", [])}}

            return {"status": "error", "error": f"Unsupported action: {action}"}

        except Exception as e:
            return {"status": "error", "error": f"Facebook Node Failed: {str(e)}"}


# ============================================
# LINKEDIN NODE
# ============================================
@register_node("linkedin_node")
class LinkedInNode(BaseNode):
    """
    LinkedIn integration for personal profiles and company pages.
    """
    node_type = "linkedin_node"
    version = "1.0.0"
    category = "social_media"
    credentials_required = ["linkedin_auth"]

    inputs = {
        "action": {
            "type": "dropdown",
            "default": "create_post",
            "options": ["create_post", "get_profile"],
            "description": "LinkedIn action"
        },
        "author_urn": {
            "type": "string",
            "optional": True,
            "description": "URN of person or organization (e.g., urn:li:person:123)"
        },
        "text": {
            "type": "string",
            "optional": True
        },
        "article_url": {
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
            creds = await self.get_credential("linkedin_auth")
            access_token = creds.get("access_token")
            
            if not access_token:
                return {"status": "error", "error": "LinkedIn access token required"}

            base_url = "https://api.linkedin.com/v2"
            headers = {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json",
                "X-Restli-Protocol-Version": "2.0.0"
            }
            
            action = self.get_config("action", "create_post")

            async with aiohttp.ClientSession() as session:
                if action == "create_post":
                    author = self.get_config("author_urn")
                    text = self.get_config("text")
                    article_url = self.get_config("article_url")
                    
                    if not author or not text:
                        return {"status": "error", "error": "author_urn (urn:li:person:...) and text required"}
                    
                    payload = {
                        "author": author,
                        "lifecycleState": "PUBLISHED",
                        "specificContent": {
                            "com.linkedin.ugc.ShareContent": {
                                "shareCommentary": {
                                    "text": text
                                },
                                "shareMediaCategory": "NONE"
                            }
                        },
                        "visibility": {
                            "com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"
                        }
                    }
                    
                    if article_url:
                        payload["specificContent"]["com.linkedin.ugc.ShareContent"]["shareMediaCategory"] = "ARTICLE"
                        payload["specificContent"]["com.linkedin.ugc.ShareContent"]["media"] = [
                            {
                                "status": "READY",
                                "originalUrl": article_url
                            }
                        ]
                    
                    url = f"{base_url}/ugcPosts"
                    async with session.post(url, headers=headers, json=payload) as resp:
                        if resp.status != 201:
                            error_text = await resp.text()
                            return {"status": "error", "error": f"LinkedIn API Error {resp.status}: {error_text}"}
                        res_data = await resp.json()
                        return {"status": "success", "data": {"result": res_data}}

                elif action == "get_profile":
                    url = f"{base_url}/me"
                    async with session.get(url, headers=headers) as resp:
                         if resp.status != 200:
                            error_text = await resp.text()
                            return {"status": "error", "error": f"LinkedIn API Error {resp.status}: {error_text}"}
                         res_data = await resp.json()
                         return {"status": "success", "data": {"result": res_data}}

            return {"status": "error", "error": f"Unsupported action: {action}"}

        except Exception as e:
            return {"status": "error", "error": f"LinkedIn Node Failed: {str(e)}"}


# ============================================
# REDDIT NODE
# ============================================
@register_node("reddit_node")
class RedditNode(BaseNode):
    """
    Reddit API integration for posting and reading.
    """
    node_type = "reddit_node"
    version = "1.0.0"
    category = "social_media"
    credentials_required = ["reddit_auth"]

    inputs = {
        "action": {
            "type": "dropdown",
            "default": "submit_post",
            "options": ["submit_post", "get_subreddit_posts", "get_user_info"],
            "description": "Reddit action"
        },
        "subreddit": {
            "type": "string",
            "optional": True,
            "description": "Subreddit name without r/"
        },
        "title": {
            "type": "string",
            "optional": True
        },
        "content": {
            "type": "string",
            "optional": True,
            "description": "Text body or URL"
        },
        "kind": {
            "type": "dropdown",
            "default": "self",
            "options": ["self", "link", "image"],
            "description": "Post type (self=text)"
        }
    }

    outputs = {
        "result": {"type": "any"},
        "status": {"type": "string"}
    }

    async def execute(self, input_data: Any, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        try:
            creds = await self.get_credential("reddit_auth")
            access_token = creds.get("access_token")
            
            if not access_token:
                return {"status": "error", "error": "Reddit access token required"}

            base_url = "https://oauth.reddit.com"
            headers = {
                "Authorization": f"Bearer {access_token}",
                "User-Agent": "StudioAutomation/1.0"
            }
            
            action = self.get_config("action", "submit_post")

            async with aiohttp.ClientSession() as session:
                if action == "submit_post":
                    subreddit = self.get_config("subreddit")
                    title = self.get_config("title")
                    content = self.get_config("content")
                    kind = self.get_config("kind", "self")
                    
                    if not subreddit or not title:
                        return {"status": "error", "error": "subreddit and title required"}
                    
                    payload = {
                        "sr": subreddit,
                        "title": title,
                        "kind": kind
                    }
                    
                    if kind == "self":
                        payload["text"] = content
                    else:
                        payload["url"] = content
                        
                    url = f"{base_url}/api/submit"
                    async with session.post(url, headers=headers, data=payload) as resp:
                        if resp.status != 200:
                            error_text = await resp.text()
                            return {"status": "error", "error": f"Reddit API Error {resp.status}: {error_text}"}
                        res_data = await resp.json()
                        return {"status": "success", "data": {"result": res_data}}

                elif action == "get_subreddit_posts":
                    subreddit = self.get_config("subreddit")
                    if not subreddit:
                         return {"status": "error", "error": "subreddit required"}
                         
                    url = f"{base_url}/r/{subreddit}/new"
                    async with session.get(url, headers=headers) as resp:
                        if resp.status != 200:
                            error_text = await resp.text()
                            return {"status": "error", "error": f"Reddit API Error {resp.status}: {error_text}"}
                        res_data = await resp.json()
                        return {"status": "success", "data": {"result": res_data.get("data", {}).get("children", [])}}

            return {"status": "error", "error": f"Unsupported action: {action}"}

        except Exception as e:
            return {"status": "error", "error": f"Reddit Node Failed: {str(e)}"}


# ============================================
# PINTEREST NODE
# ============================================
@register_node("pinterest_node")
class PinterestNode(BaseNode):
    """
    Pinterest integration for creating pins and boards.
    """
    node_type = "pinterest_node"
    version = "1.0.0"
    category = "social_media"
    credentials_required = ["pinterest_auth"]

    inputs = {
        "action": {
            "type": "dropdown",
            "default": "create_pin",
            "options": ["create_pin", "create_board", "list_boards"],
            "description": "Pinterest action"
        },
        "board_id": {
            "type": "string",
            "optional": True
        },
        "image_url": {
            "type": "string",
            "optional": True
        },
        "title": {
            "type": "string",
            "optional": True
        },
        "description": {
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
            creds = await self.get_credential("pinterest_auth")
            access_token = creds.get("access_token")
            
            if not access_token:
                return {"status": "error", "error": "Pinterest access token required"}

            base_url = "https://api.pinterest.com/v5"
            headers = {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json"
            }
            
            action = self.get_config("action", "create_pin")

            async with aiohttp.ClientSession() as session:
                if action == "create_pin":
                    board_id = self.get_config("board_id")
                    image_url = self.get_config("image_url")
                    title = self.get_config("title")
                    
                    if not board_id or not image_url:
                        return {"status": "error", "error": "board_id and image_url required"}
                    
                    payload = {
                        "board_id": board_id,
                        "media_source": {
                            "source_type": "image_url",
                            "url": image_url
                        },
                        "title": title
                    }
                    description = self.get_config("description")
                    if description:
                         payload["description"] = description
                         
                    url = f"{base_url}/pins"
                    async with session.post(url, headers=headers, json=payload) as resp:
                        if resp.status != 201:
                            error_text = await resp.text()
                            return {"status": "error", "error": f"Pinterest API Error {resp.status}: {error_text}"}
                        res_data = await resp.json()
                        return {"status": "success", "data": {"result": res_data}}
                
                elif action == "list_boards":
                    url = f"{base_url}/boards"
                    async with session.get(url, headers=headers) as resp:
                        if resp.status != 200:
                            error_text = await resp.text()
                            return {"status": "error", "error": f"Pinterest API Error {resp.status}: {error_text}"}
                        res_data = await resp.json()
                        return {"status": "success", "data": {"result": res_data.get("items", [])}}

            return {"status": "error", "error": f"Unsupported action: {action}"}

        except Exception as e:
            return {"status": "error", "error": f"Pinterest Node Failed: {str(e)}"}