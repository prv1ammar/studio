"""
Clerk Node - Studio Standard
Batch 61: Identity & Security
"""
from typing import Any, Dict, Optional, List
import aiohttp
from ...base import BaseNode
from ...registry import register_node

@register_node("clerk_node")
class ClerkNode(BaseNode):
    """
    Modern developer-first identity management via Clerk.
    Supports user listings, organization management, and session auditing.
    """
    node_type = "clerk_node"
    version = "1.0.0"
    category = "security"
    credentials_required = ["clerk_auth"]

    inputs = {
        "action": {
            "type": "dropdown",
            "default": "list_users",
            "options": ["list_users", "get_user", "list_organizations", "list_sessions"],
            "description": "Clerk action"
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
            creds = await self.get_credential("clerk_auth")
            secret_key = creds.get("secret_key") if creds else self.get_config("secret_key")
            
            if not secret_key:
                return {"status": "error", "error": "Clerk Secret Key is required."}

            headers = {
                "Authorization": f"Bearer {secret_key}",
                "Content-Type": "application/json"
            }
            
            base_url = "https://api.clerk.com/v1"
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

                elif action == "list_organizations":
                    url = f"{base_url}/organizations"
                    async with session.get(url, headers=headers) as resp:
                        res_data = await resp.json()
                        # Clerk might wrap this in a 'data' field
                        items = res_data.get("data", res_data) if isinstance(res_data, dict) else res_data
                        return {"status": "success", "data": {"result": items, "count": len(items)}}

                elif action == "list_sessions":
                    url = f"{base_url}/sessions"
                    async with session.get(url, headers=headers) as resp:
                        res_data = await resp.json()
                        return {"status": "success", "data": {"result": res_data, "count": len(res_data)}}

                return {"status": "error", "error": f"Unsupported Clerk action: {action}"}

        except Exception as e:
            return {"status": "error", "error": f"Clerk Node Failed: {str(e)}"}
