"""
Drift Node - Studio Standard (Universal Method)
Batch 109: Analytics & Support
"""
from typing import Any, Dict, Optional
import aiohttp
from ...base import BaseNode
from ...registry import register_node

@register_node("drift_node")
class DriftNode(BaseNode):
    """
    Drift integration for conversational marketing.
    """
    node_type = "drift_node"
    version = "1.0.0"
    category = "analytics"
    credentials_required = ["drift_auth"]

    inputs = {
        "action": {
            "type": "dropdown",
            "default": "create_contact",
            "options": ["create_contact", "get_contact"],
            "description": "Drift action"
        },
        "email": {
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
            creds = await self.get_credential("drift_auth")
            access_token = creds.get("access_token")
            
            if not access_token:
                return {"status": "error", "error": "Drift access token required"}

            base_url = "https://driftapi.com"
            headers = {"Authorization": f"Bearer {access_token}", "Content-Type": "application/json"}
            
            action = self.get_config("action", "create_contact")

            async with aiohttp.ClientSession() as session:
                if action == "create_contact":
                    email = self.get_config("email")
                    if not email: return {"status": "error", "error": "email required"}
                    
                    payload = {"email": email}
                    
                    url = f"{base_url}/contacts"
                    async with session.post(url, headers=headers, json=payload) as resp:
                         if resp.status not in [200, 201]:
                            error_text = await resp.text()
                            return {"status": "error", "error": f"Drift API Error {resp.status}: {error_text}"}
                         res_data = await resp.json()
                         return {"status": "success", "data": {"result": res_data.get("data", {})}}
                
                elif action == "get_contact":
                     email = self.get_config("email")
                     if not email: return {"status": "error", "error": "email required"}
                     
                     url = f"{base_url}/contacts?email={email}"
                     async with session.get(url, headers=headers) as resp:
                         res_data = await resp.json()
                         return {"status": "success", "data": {"result": res_data.get("data", {})}}

            return {"status": "error", "error": f"Unsupported action: {action}"}

        except Exception as e:
            return {"status": "error", "error": f"Drift Node Failed: {str(e)}"}
