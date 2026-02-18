"""
LinkedIn Node - Studio Standard (Universal Method)
Batch 106: Social Media
"""
from typing import Any, Dict, Optional
import aiohttp
from ..base import BaseNode
from ..registry import register_node

@register_node("linkedin_node")
class LinkedInNode(BaseNode):
    """
    LinkedIn integration for personal profiles and company pages.
    """
    node_type = "linkedin_node"
    version = "1.0.0"
    category = "social_media"
    credentials_required = ["linkedin_auth"]


    properties = [
        {
            'displayName': 'Operation',
            'name': 'operation',
            'type': 'options',
            'default': 'create_post',
            'options': [
                {'name': 'Create Post', 'value': 'create_post'},
                {'name': 'Get Profile', 'value': 'get_profile'},
            ],
            'description': 'LinkedIn action',
        },
        {
            'displayName': 'Article Url',
            'name': 'article_url',
            'type': 'string',
            'default': '',
        },
        {
            'displayName': 'Author Urn',
            'name': 'author_urn',
            'type': 'string',
            'default': '',
            'description': 'URN of person or organization (e.g., urn:li:person:123)',
        },
        {
            'displayName': 'Text',
            'name': 'text',
            'type': 'string',
            'default': '',
        },
    ]
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