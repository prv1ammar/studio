"""
Okta Node - Studio Standard
Batch 61: Identity & Security
"""
from typing import Any, Dict, Optional, List
import aiohttp
from ..base import BaseNode
from ..registry import register_node

@register_node("okta_node")
class OktaNode(BaseNode):
    """
    Enterprise Identity & Access Management via Okta.
    Supports user lifecycle management and system log auditing.
    """
    node_type = "okta_node"
    version = "1.0.0"
    category = "security"
    credentials_required = ["okta_auth"]


    properties = [
        {
            'displayName': 'Operation',
            'name': 'operation',
            'type': 'options',
            'default': 'list_users',
            'options': [
                {'name': 'List Users', 'value': 'list_users'},
                {'name': 'Get User', 'value': 'get_user'},
                {'name': 'List Groups', 'value': 'list_groups'},
                {'name': 'Get Logs', 'value': 'get_logs'},
            ],
            'description': 'Okta action',
        },
        {
            'displayName': 'Domain',
            'name': 'domain',
            'type': 'string',
            'default': '',
            'description': 'Your Okta Domain (e.g. 'company.okta.com')',
            'required': True,
        },
        {
            'displayName': 'User Id',
            'name': 'user_id',
            'type': 'string',
            'default': '',
        },
    ]
    inputs = {
        "action": {
            "type": "dropdown",
            "default": "list_users",
            "options": ["list_users", "get_user", "list_groups", "get_logs"],
            "description": "Okta action"
        },
        "domain": {
            "type": "string",
            "required": True,
            "description": "Your Okta Domain (e.g. 'company.okta.com')"
        },
        "user_id": {
            "type": "string",
            "optional": True
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
            creds = await self.get_credential("okta_auth")
            api_token = creds.get("api_token") if creds else self.get_config("api_token")
            domain = self.get_config("domain").rstrip("/")
            
            if not api_token or not domain:
                return {"status": "error", "error": "Okta API Token (SSWS) and Domain are required."}

            headers = {
                "Authorization": f"SSWS {api_token}",
                "Accept": "application/json",
                "Content-Type": "application/json"
            }
            
            base_url = f"https://{domain}/api/v1"
            action = self.get_config("action", "list_users")

            async with aiohttp.ClientSession() as session:
                if action == "list_users":
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

                elif action == "list_groups":
                    url = f"{base_url}/groups"
                    async with session.get(url, headers=headers) as resp:
                        res_data = await resp.json()
                        return {"status": "success", "data": {"result": res_data, "count": len(res_data)}}

                elif action == "get_logs":
                    # Logs are in /api/v1/logs
                    url = f"{base_url}/logs"
                    async with session.get(url, headers=headers) as resp:
                        res_data = await resp.json()
                        return {"status": "success", "data": {"result": res_data, "count": len(res_data)}}

                return {"status": "error", "error": f"Unsupported Okta action: {action}"}

        except Exception as e:
            return {"status": "error", "error": f"Okta Node Failed: {str(e)}"}