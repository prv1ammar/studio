"""
Wise Node - Studio Standard
Batch 58: Financial Services
"""
from typing import Any, Dict, Optional, List
import aiohttp
from ..base import BaseNode
from ..registry import register_node

@register_node("wise_node")
class WiseNode(BaseNode):
    """
    Automate international transfers and currency management via Wise.
    """
    node_type = "wise_node"
    version = "1.0.0"
    category = "finance"
    credentials_required = ["wise_auth"]


    properties = [
        {
            'displayName': 'Operation',
            'name': 'operation',
            'type': 'options',
            'default': 'list_profiles',
            'options': [
                {'name': 'List Profiles', 'value': 'list_profiles'},
                {'name': 'Get Accounts', 'value': 'get_accounts'},
                {'name': 'Create Quote', 'value': 'create_quote'},
                {'name': 'List Transfers', 'value': 'list_transfers'},
            ],
            'description': 'Wise action to perform',
        },
        {
            'displayName': 'Is Sandbox',
            'name': 'is_sandbox',
            'type': 'boolean',
            'default': True,
            'description': 'Use Wise Sandbox environment',
        },
        {
            'displayName': 'Profile Id',
            'name': 'profile_id',
            'type': 'string',
            'default': '',
            'description': 'The specific Wise profile ID (Personal or Business)',
        },
    ]
    inputs = {
        "action": {
            "type": "dropdown",
            "default": "list_profiles",
            "options": ["list_profiles", "get_accounts", "create_quote", "list_transfers"],
            "description": "Wise action to perform"
        },
        "profile_id": {
            "type": "string",
            "optional": True,
            "description": "The specific Wise profile ID (Personal or Business)"
        },
        "is_sandbox": {
            "type": "boolean",
            "default": True,
            "description": "Use Wise Sandbox environment"
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
            creds = await self.get_credential("wise_auth")
            api_token = creds.get("api_token") if creds else self.get_config("api_token")
            is_sandbox = self.get_config("is_sandbox", True)
            
            if not api_token:
                return {"status": "error", "error": "Wise API Token is required."}

            base_url = "https://api.sandbox.transferwise.com" if is_sandbox else "https://api.transferwise.com"
            action = self.get_config("action", "list_profiles")
            profile_id = self.get_config("profile_id") or (str(input_data) if isinstance(input_data, (str, int)) and len(str(input_data)) > 5 else None)

            headers = {
                "Authorization": f"Bearer {api_token}",
                "Content-Type": "application/json"
            }
            
            async with aiohttp.ClientSession() as session:
                if action == "list_profiles":
                    url = f"{base_url}/v1/profiles"
                    async with session.get(url, headers=headers) as resp:
                        res_data = await resp.json()
                        return {"status": "success", "data": {"result": res_data, "count": len(res_data)}}

                elif action == "get_accounts":
                    if not profile_id:
                        return {"status": "error", "error": "Profile ID is required to fetch accounts."}
                    url = f"{base_url}/v1/borderless-accounts"
                    params = {"profileId": profile_id}
                    async with session.get(url, headers=headers, params=params) as resp:
                        res_data = await resp.json()
                        return {"status": "success", "data": {"result": res_data}}

                elif action == "list_transfers":
                    if not profile_id:
                        return {"status": "error", "error": "Profile ID is required to fetch transfers."}
                    url = f"{base_url}/v1/transfers"
                    params = {"offset": 0, "limit": 10, "profile": profile_id}
                    async with session.get(url, headers=headers, params=params) as resp:
                        res_data = await resp.json()
                        return {"status": "success", "data": {"result": res_data, "count": len(res_data)}}

                return {"status": "error", "error": f"Unsupported Wise action: {action}"}

        except Exception as e:
            return {"status": "error", "error": f"Wise Node Failed: {str(e)}"}