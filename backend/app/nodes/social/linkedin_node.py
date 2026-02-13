"""
LinkedIn Node - Studio Standard (Universal Method)
Batch 92: Social Media Integration (n8n Critical)
"""
from typing import Any, Dict, Optional, List
import aiohttp
from ...base import BaseNode
from ...registry import register_node

@register_node("linkedin_node")
class LinkedInNode(BaseNode):
    """
    Manage LinkedIn posts and business page operations via LinkedIn API.
    """
    node_type = "linkedin_node"
    version = "1.0.0"
    category = "social"
    credentials_required = ["linkedin_auth"]

    inputs = {
        "action": {
            "type": "dropdown",
            "default": "refresh_access_token",
            "options": ["create_text_share", "get_me", "refresh_access_token", "get_organization"],
            "description": "LinkedIn action"
        },
        "urn": {
            "type": "string",
            "optional": True,
            "description": "Person or Organization URN (e.g. urn:li:person:123)"
        },
        "text": {
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
            # 1. Authentication
            creds = await self.get_credential("linkedin_auth")
            access_token = creds.get("access_token")
            
            if not access_token:
                return {"status": "error", "error": "LinkedIn Access Token required."}

            headers = {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json",
                "X-Restli-Protocol-Version": "2.0.0"
            }
            
            # 2. Connect to Real API
            base_url = "https://api.linkedin.com/v2"
            action = self.get_config("action", "get_me")

            async with aiohttp.ClientSession() as session:
                if action == "get_me":
                    url = f"{base_url}/me"
                    async with session.get(url, headers=headers) as resp:
                        if resp.status != 200:
                            return {"status": "error", "error": f"LinkedIn Error: {resp.status}"}
                        res_data = await resp.json()
                        return {"status": "success", "data": {"result": res_data}}

                elif action == "create_text_share":
                    # This relies on ugcPosts (User Generated Content)
                    urn = self.get_config("urn")
                    text = self.get_config("text") or str(input_data)
                    
                    if not urn:
                        return {"status": "error", "error": "Author URN required (person or organization)"}
                    
                    url = f"{base_url}/ugcPosts"
                    payload = {
                        "author": urn,
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
                    async with session.post(url, headers=headers, json=payload) as resp:
                        if resp.status not in [200, 201]:
                            return {"status": "error", "error": f"LinkedIn Error: {resp.status} - {await resp.text()}"}
                        res_data = await resp.json()
                        return {"status": "success", "data": {"result": res_data}}

                return {"status": "error", "error": f"Unsupported action: {action}"}

        except Exception as e:
            return {"status": "error", "error": f"LinkedIn Node Failed: {str(e)}"}
