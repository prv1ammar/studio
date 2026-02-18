"""
Reddit Node - Studio Standard (Universal Method)
Batch 106: Social Media
"""
from typing import Any, Dict, Optional
import aiohttp
from ..base import BaseNode
from ..registry import register_node

@register_node("reddit_node")
class RedditNode(BaseNode):
    """
    Reddit API integration for posting and reading.
    """
    node_type = "reddit_node"
    version = "1.0.0"
    category = "social_media"
    credentials_required = ["reddit_auth"]


    properties = [
        {
            'displayName': 'Operation',
            'name': 'operation',
            'type': 'options',
            'default': 'submit_post',
            'options': [
                {'name': 'Submit Post', 'value': 'submit_post'},
                {'name': 'Get Subreddit Posts', 'value': 'get_subreddit_posts'},
                {'name': 'Get User Info', 'value': 'get_user_info'},
            ],
            'description': 'Reddit action',
        },
        {
            'displayName': 'Content',
            'name': 'content',
            'type': 'string',
            'default': '',
            'description': 'Text body or URL',
        },
        {
            'displayName': 'Kind',
            'name': 'kind',
            'type': 'options',
            'default': 'self',
            'options': [
                {'name': 'Self', 'value': 'self'},
                {'name': 'Link', 'value': 'link'},
                {'name': 'Image', 'value': 'image'},
            ],
            'description': 'Post type (self=text)',
        },
        {
            'displayName': 'Subreddit',
            'name': 'subreddit',
            'type': 'string',
            'default': '',
            'description': 'Subreddit name without r/',
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