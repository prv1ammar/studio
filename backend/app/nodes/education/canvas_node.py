"""
Canvas LMS Node - Studio Standard
Batch 75: Education & EdTech
"""
from typing import Any, Dict, Optional, List
import aiohttp
from ..base import BaseNode
from ..registry import register_node

@register_node("canvas_node")
class CanvasNode(BaseNode):
    """
    Manage courses, assignments, and users via the Canvas LMS API.
    """
    node_type = "canvas_node"
    version = "1.0.0"
    category = "education"
    credentials_required = ["canvas_auth"]


    properties = [
        {
            'displayName': 'Operation',
            'name': 'operation',
            'type': 'options',
            'default': 'list_courses',
            'options': [
                {'name': 'List Courses', 'value': 'list_courses'},
                {'name': 'List Assignments', 'value': 'list_assignments'},
                {'name': 'Get Course', 'value': 'get_course'},
                {'name': 'List Users', 'value': 'list_users'},
            ],
            'description': 'Canvas action',
        },
        {
            'displayName': 'Base Url',
            'name': 'base_url',
            'type': 'string',
            'default': '',
            'description': 'Institutional Canvas URL (e.g. https://canvas.instructure.com)',
            'required': True,
        },
        {
            'displayName': 'Course Id',
            'name': 'course_id',
            'type': 'string',
            'default': '',
        },
    ]
    inputs = {
        "action": {
            "type": "dropdown",
            "default": "list_courses",
            "options": ["list_courses", "list_assignments", "get_course", "list_users"],
            "description": "Canvas action"
        },
        "base_url": {
            "type": "string",
            "required": True,
            "description": "Institutional Canvas URL (e.g. https://canvas.instructure.com)"
        },
        "course_id": {
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
            creds = await self.get_credential("canvas_auth")
            api_token = creds.get("api_token") if creds else self.get_config("api_token")
            
            if not api_token:
                return {"status": "error", "error": "Canvas API Token is required."}

            headers = {
                "Authorization": f"Bearer {api_token}",
                "Accept": "application/json"
            }
            
            domain = self.get_config("base_url").rstrip("/")
            api_url = f"{domain}/api/v1"
            action = self.get_config("action", "list_courses")

            async with aiohttp.ClientSession() as session:
                if action == "list_courses":
                    url = f"{api_url}/courses"
                    async with session.get(url, headers=headers) as resp:
                        res_data = await resp.json()
                        return {"status": "success", "data": {"result": res_data, "count": len(res_data) if isinstance(res_data, list) else 0}}

                elif action == "list_assignments":
                    c_id = self.get_config("course_id") or str(input_data)
                    if not c_id:
                        return {"status": "error", "error": "course_id is required to list assignments."}
                    url = f"{api_url}/courses/{c_id}/assignments"
                    async with session.get(url, headers=headers) as resp:
                        res_data = await resp.json()
                        return {"status": "success", "data": {"result": res_data, "count": len(res_data) if isinstance(res_data, list) else 0}}

                elif action == "list_users":
                    c_id = self.get_config("course_id")
                    url = f"{api_url}/courses/{c_id}/users" if c_id else f"{api_url}/accounts/self/users"
                    async with session.get(url, headers=headers) as resp:
                        res_data = await resp.json()
                        return {"status": "success", "data": {"result": res_data, "count": len(res_data) if isinstance(res_data, list) else 0}}

                return {"status": "error", "error": f"Unsupported action: {action}"}

        except Exception as e:
            return {"status": "error", "error": f"Canvas Node Failed: {str(e)}"}