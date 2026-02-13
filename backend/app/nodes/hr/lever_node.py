"""
Lever Node - Studio Standard
Batch 64: HR & Recruiting
"""
from typing import Any, Dict, Optional, List
import aiohttp
import base64
from ...base import BaseNode
from ...registry import register_node

@register_node("lever_node")
class LeverNode(BaseNode):
    """
    Automate recruitment workflows and candidate management via Lever ATS.
    """
    node_type = "lever_node"
    version = "1.0.0"
    category = "hr"
    credentials_required = ["lever_auth"]

    inputs = {
        "action": {
            "type": "dropdown",
            "default": "list_candidates",
            "options": ["list_candidates", "get_candidate", "list_opportunities", "create_candidate"],
            "description": "Lever action to perform"
        },
        "candidate_id": {
            "type": "string",
            "optional": True,
            "description": "Unique ID of the candidate"
        },
        "email": {
            "type": "string",
            "optional": True,
            "description": "Candidate email for creation or filtering"
        },
        "limit": {
            "type": "number",
            "default": 10
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
            creds = await self.get_credential("lever_auth")
            api_key = creds.get("api_key") if creds else self.get_config("api_key")
            
            if not api_key:
                return {"status": "error", "error": "Lever API Key (API Key or Access Token) is required."}

            headers = {
                "Authorization": f"Bearer {api_key}",
                "Accept": "application/json"
            }
            
            base_url = "https://api.lever.co/v1"
            action = self.get_config("action", "list_candidates")
            limit = int(self.get_config("limit", 10))

            async with aiohttp.ClientSession() as session:
                if action == "list_candidates":
                    url = f"{base_url}/candidates"
                    params = {"limit": limit}
                    async with session.get(url, headers=headers, params=params) as resp:
                        res_data = await resp.json()
                        data = res_data.get("data", [])
                        return {"status": "success", "data": {"result": data, "count": len(data)}}

                elif action == "get_candidate":
                    candidate_id = self.get_config("candidate_id") or str(input_data)
                    url = f"{base_url}/candidates/{candidate_id}"
                    async with session.get(url, headers=headers) as resp:
                        res_data = await resp.json()
                        return {"status": "success", "data": {"result": res_data.get("data")}}

                elif action == "list_opportunities":
                    url = f"{base_url}/opportunities"
                    params = {"limit": limit}
                    async with session.get(url, headers=headers, params=params) as resp:
                        res_data = await resp.json()
                        data = res_data.get("data", [])
                        return {"status": "success", "data": {"result": data, "count": len(data)}}

                elif action == "create_candidate":
                    url = f"{base_url}/candidates"
                    name = str(input_data) if input_data else "New Candidate"
                    email = self.get_config("email")
                    payload = {
                        "name": name,
                        "emails": [email] if email else []
                    }
                    async with session.post(url, headers=headers, json=payload) as resp:
                        res_data = await resp.json()
                        return {"status": "success", "data": {"result": res_data.get("data"), "status": "created"}}

                return {"status": "error", "error": f"Unsupported Lever action: {action}"}

        except Exception as e:
            return {"status": "error", "error": f"Lever Node Failed: {str(e)}"}
