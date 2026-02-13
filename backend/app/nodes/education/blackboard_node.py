"""
Blackboard Node - Studio Standard
Batch 75: Education & EdTech
"""
from typing import Any, Dict, Optional, List
import aiohttp
from ...base import BaseNode
from ...registry import register_node

@register_node("blackboard_node")
class BlackboardNode(BaseNode):
    """
    Access institutional learning data via the Blackboard Learn REST API.
    """
    node_type = "blackboard_node"
    version = "1.0.0"
    category = "education"
    credentials_required = ["blackboard_auth"]

    inputs = {
        "action": {
            "type": "dropdown",
            "default": "list_courses",
            "options": ["list_courses", "get_course", "list_users", "get_gradebook"],
            "description": "Blackboard action"
        },
        "base_url": {
            "type": "string",
            "required": True,
            "description": "Institutional Blackboard URL"
        },
        "course_id": {
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
            creds = await self.get_credential("blackboard_auth")
            api_token = creds.get("api_token") if creds else self.get_config("api_token")
            
            if not api_token:
                return {"status": "error", "error": "Blackboard API Token is required."}

            headers = {
                "Authorization": f"Bearer {api_token}",
                "Content-Type": "application/json"
            }
            
            domain = self.get_config("base_url").rstrip("/")
            api_url = f"{domain}/learn/api/public/v1"
            action = self.get_config("action", "list_courses")

            async with aiohttp.ClientSession() as session:
                if action == "list_courses":
                    url = f"{api_url}/courses"
                    async with session.get(url, headers=headers) as resp:
                        res_data = await resp.json()
                        return {"status": "success", "data": {"result": res_data.get("results", [])}}

                elif action == "list_users":
                    c_id = self.get_config("course_id")
                    url = f"{api_url}/courses/{c_id}/users" if c_id else f"{api_url}/users"
                    async with session.get(url, headers=headers) as resp:
                        res_data = await resp.json()
                        return {"status": "success", "data": {"result": res_data.get("results", [])}}

                return {"status": "error", "error": f"Unsupported action: {action}"}

        except Exception as e:
            return {"status": "error", "error": f"Blackboard Node Failed: {str(e)}"}
