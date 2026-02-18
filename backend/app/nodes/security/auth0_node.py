"""
Auth0 Node - Studio Standard
Batch 61: Identity & Security
"""
from typing import Any, Dict, Optional, List
import aiohttp
from ..base import BaseNode
from ..registry import register_node

@register_node("auth0_node")
class Auth0Node(BaseNode):
    """
    Manage users and security logs via Auth0 Management API.
    """
    node_type = "auth0_node"
    version = "1.0.0"
    category = "security"
    credentials_required = ["auth0_auth"]


    properties = [
        {
            'displayName': 'Operation',
            'name': 'operation',
            'type': 'options',
            'default': 'get_users',
            'options': [
                {'name': 'Get Users', 'value': 'get_users'},
                {'name': 'Get User', 'value': 'get_user'},
                {'name': 'Get Logs', 'value': 'get_logs'},
                {'name': 'Create User', 'value': 'create_user'},
            ],
            'description': 'Auth0 action',
        },
        {
            'displayName': 'Domain',
            'name': 'domain',
            'type': 'string',
            'default': '',
            'description': 'Your Auth0 Domain (e.g. 'dev-123.us.auth0.com')',
            'required': True,
        },
        {
            'displayName': 'Email',
            'name': 'email',
            'type': 'string',
            'default': '',
            'description': 'User email for creation',
        },
        {
            'displayName': 'User Id',
            'name': 'user_id',
            'type': 'string',
            'default': '',
            'description': 'Target User ID',
        },
    ]
    inputs = {
        "action": {
            "type": "dropdown",
            "default": "get_users",
            "options": ["get_users", "get_user", "get_logs", "create_user"],
            "description": "Auth0 action"
        },
        "domain": {
            "type": "string",
            "required": True,
            "description": "Your Auth0 Domain (e.g. 'dev-123.us.auth0.com')"
        },
        "user_id": {
            "type": "string",
            "optional": True,
            "description": "Target User ID"
        },
        "email": {
            "type": "string",
            "optional": True,
            "description": "User email for creation"
        }
    }

    outputs = {
        "result": {"type": "any"},
        "status": {"type": "string"},
        "count": {"type": "number"}
    }

    async def execute(self, input_data: Any, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        try:
            # 1. Resolve Auth
            creds = await self.get_credential("auth0_auth")
            # For Auth0 Management API, we usually need an M2M token. 
            # This node assumes the user provides the M2M Access Token or 
            # we handle the token exchange if credentials are full.
            api_token = creds.get("api_token") if creds else self.get_config("api_token")
            domain = self.get_config("domain").rstrip("/")
            
            if not api_token or not domain:
                return {"status": "error", "error": "Auth0 API Token and Domain are required."}

            headers = {
                "Authorization": f"Bearer {api_token}",
                "Content-Type": "application/json"
            }
            
            base_url = f"https://{domain}/api/v2"
            action = self.get_config("action", "get_users")

            async with aiohttp.ClientSession() as session:
                if action == "get_users":
                    url = f"{base_url}/users"
                    async with session.get(url, headers=headers) as resp:
                        res_data = await resp.json()
                        return {"status": "success", "data": {"result": res_data, "count": len(res_data)}}

                elif action == "get_user":
                    user_id = self.get_config("user_id") or str(input_data)
                    url = f"{base_url}/users/{user_id}"
                    async with session.get(url, headers=headers) as resp:
                        res_data = await resp.json()
                        return {"status": "success", "data": {"result": res_data}}

                elif action == "get_logs":
                    url = f"{base_url}/logs"
                    async with session.get(url, headers=headers) as resp:
                        res_data = await resp.json()
                        return {"status": "success", "data": {"result": res_data, "count": len(res_data)}}

                elif action == "create_user":
                    url = f"{base_url}/users"
                    email = self.get_config("email") or str(input_data)
                    payload = {
                        "email": email,
                        "connection": "Username-Password-Authentication", # Default
                        "password": "TemporaryPassword123!", # Should be dynamic or handled via invite
                        "email_verified": False
                    }
                    async with session.post(url, headers=headers, json=payload) as resp:
                        res_data = await resp.json()
                        return {"status": "success", "data": {"result": res_data, "status": "created"}}

                return {"status": "error", "error": f"Unsupported Auth0 action: {action}"}

        except Exception as e:
            return {"status": "error", "error": f"Auth0 Node Failed: {str(e)}"}