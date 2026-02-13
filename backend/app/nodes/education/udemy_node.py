"""
Udemy Node - Studio Standard
Batch 81: Leisure, Health & Education
"""
from typing import Any, Dict, Optional, List
import aiohttp
from ...base import BaseNode
from ...registry import register_node

@register_node("udemy_node")
class UdemyNode(BaseNode):
    """
    Search and manage courses via Udemy Affiliate/Business API.
    """
    node_type = "udemy_node"
    version = "1.0.0"
    category = "education"
    credentials_required = ["udemy_auth"]

    inputs = {
        "action": {
            "type": "dropdown",
            "default": "search_courses",
            "options": ["search_courses", "get_course_details", "get_my_courses"],
            "description": "Udemy action"
        },
        "query": {
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
            creds = await self.get_credential("udemy_auth")
            client_id = creds.get("client_id")
            client_secret = creds.get("client_secret")
            
            if not client_id or not client_secret:
                return {"status": "error", "error": "Udemy Client ID and Secret are required."}

            import base64
            auth = base64.b64encode(f"{client_id}:{client_secret}".encode()).decode()
            headers = {"Authorization": f"Basic {auth}", "Accept": "application/json"}
            base_url = "https://www.udemy.com/api-2.0"
            action = self.get_config("action", "search_courses")

            async with aiohttp.ClientSession() as session:
                if action == "search_courses":
                    q = self.get_config("query") or str(input_data)
                    url = f"{base_url}/courses/"
                    params = {"search": q}
                    async with session.get(url, headers=headers, params=params) as resp:
                        res_data = await resp.json()
                        return {"status": "success", "data": {"result": res_data.get("results", [])}}
                
                return {"status": "error", "error": f"Unsupported action: {action}"}
        except Exception as e:
            return {"status": "error", "error": f"Udemy Node Failed: {str(e)}"}
