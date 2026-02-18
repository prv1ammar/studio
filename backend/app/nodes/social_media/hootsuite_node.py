"""
Hootsuite Node - Studio Standard (Universal Method)
Batch 106: Social Media
"""
from typing import Any, Dict, Optional
import aiohttp
from ..base import BaseNode
from ..registry import register_node

@register_node("hootsuite_node")
class HootsuiteNode(BaseNode):
    """
    Hootsuite integration for managing social media.
    """
    node_type = "hootsuite_node"
    version = "1.0.0"
    category = "social_media"
    credentials_required = ["hootsuite_auth"]


    properties = [
        {
            'displayName': 'Operation',
            'name': 'operation',
            'type': 'options',
            'default': 'create_message',
            'options': [
                {'name': 'Create Message', 'value': 'create_message'},
                {'name': 'Get Profiles', 'value': 'get_profiles'},
            ],
            'description': 'Hootsuite action',
        },
        {
            'displayName': 'Social Profile Ids',
            'name': 'social_profile_ids',
            'type': 'string',
            'default': '',
            'description': 'Comma separated profile IDs',
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
            "default": "create_message",
            "options": ["create_message", "get_profiles"],
            "description": "Hootsuite action"
        },
        "social_profile_ids": {
            "type": "string",
            "optional": True,
            "description": "Comma separated profile IDs"
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
            creds = await self.get_credential("hootsuite_auth")
            access_token = creds.get("access_token")
            
            if not access_token:
                return {"status": "error", "error": "Hootsuite access token required"}

            base_url = "https://platform.hootsuite.com/v1"
            headers = {"Authorization": f"Bearer {access_token}"}
            
            action = self.get_config("action", "create_message")

            async with aiohttp.ClientSession() as session:
                if action == "create_message":
                    social_profile_ids = self.get_config("social_profile_ids")
                    text = self.get_config("text")
                    
                    if not social_profile_ids or not text:
                        return {"status": "error", "error": "social_profile_ids and text required"}
                    
                    payload = {
                        "text": text,
                        "socialProfileIds": [pid.strip() for pid in social_profile_ids.split(",") if pid.strip()]
                    }
                    
                    url = f"{base_url}/messages"
                    async with session.post(url, headers=headers, json=payload) as resp:
                        if resp.status not in [200, 201]:
                            error_text = await resp.text()
                            return {"status": "error", "error": f"Hootsuite API Error {resp.status}: {error_text}"}
                        res_data = await resp.json()
                        return {"status": "success", "data": {"result": res_data}}

                elif action == "get_profiles":
                     url = f"{base_url}/socialProfiles"
                     async with session.get(url, headers=headers) as resp:
                        if resp.status != 200:
                            error_text = await resp.text()
                            return {"status": "error", "error": f"Hootsuite API Error {resp.status}: {error_text}"}
                        res_data = await resp.json()
                        return {"status": "success", "data": {"result": res_data.get("data", [])}}

            return {"status": "error", "error": f"Unsupported action: {action}"}

        except Exception as e:
            return {"status": "error", "error": f"Hootsuite Node Failed: {str(e)}"}