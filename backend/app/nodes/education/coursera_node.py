"""
Coursera Node - Studio Standard
Batch 75: Education & EdTech
"""
from typing import Any, Dict, Optional, List
import aiohttp
from ...base import BaseNode
from ...registry import register_node

@register_node("coursera_node")
class CourseraNode(BaseNode):
    """
    Search for learning content and certifications via the Coursera Catalog API.
    """
    node_type = "coursera_node"
    version = "1.0.0"
    category = "education"
    credentials_required = ["coursera_auth"]

    inputs = {
        "action": {
            "type": "dropdown",
            "default": "search_courses",
            "options": ["search_courses", "get_course_details", "list_partners"],
            "description": "Coursera action"
        },
        "query": {
            "type": "string",
            "optional": True,
            "description": "Topic or keyword (e.g. Machine Learning)"
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
            creds = await self.get_credential("coursera_auth")
            api_key = creds.get("api_key") if creds else self.get_config("api_key")
            
            # Note: Coursera Catalog API is often public or requires a partner key.
            headers = {"Accept": "application/json"}
            if api_key:
                headers["Authorization"] = f"Bearer {api_key}"
                
            base_url = "https://api.coursera.org/api/catalog.v1"
            action = self.get_config("action", "search_courses")

            async with aiohttp.ClientSession() as session:
                if action == "search_courses":
                    query = self.get_config("query") or str(input_data)
                    url = f"{base_url}/courses"
                    params = {"q": "search", "query": query, "fields": "name,slug,description,partnerIds"}
                    async with session.get(url, headers=headers, params=params) as resp:
                        res_data = await resp.json()
                        elements = res_data.get("elements", [])
                        return {"status": "success", "data": {"result": elements, "count": len(elements)}}

                elif action == "list_partners":
                    url = f"{base_url}/partners"
                    async with session.get(url, headers=headers) as resp:
                        res_data = await resp.json()
                        elements = res_data.get("elements", [])
                        return {"status": "success", "data": {"result": elements, "count": len(elements)}}

                return {"status": "error", "error": f"Unsupported action: {action}"}

        except Exception as e:
            return {"status": "error", "error": f"Coursera Node Failed: {str(e)}"}
