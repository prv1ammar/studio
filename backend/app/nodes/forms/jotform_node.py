"""
JotForm Node - Studio Standard
Batch 57: Forms & Surveys
"""
from typing import Any, Dict, Optional, List
import aiohttp
from ...base import BaseNode
from ...registry import register_node

@register_node("jotform_node")
class JotFormNode(BaseNode):
    """
    Interact with JotForm API to manage forms and submissions.
    """
    node_type = "jotform_node"
    version = "1.0.0"
    category = "forms"
    credentials_required = ["jotform_auth"]

    inputs = {
        "action": {
            "type": "dropdown",
            "default": "get_forms",
            "options": ["get_forms", "get_form_details", "get_submissions", "get_form_questions"],
            "description": "JotForm action to perform"
        },
        "form_id": {
            "type": "string",
            "optional": True,
            "description": "Unique ID of the JotForm"
        },
        "limit": {
            "type": "number",
            "default": 10
        }
    }

    outputs = {
        "result": {"type": "any"},
        "count": {"type": "number"},
        "status": {"type": "string"}
    }

    async def execute(self, input_data: Any, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        try:
            # 1. Resolve Auth
            creds = await self.get_credential("jotform_auth")
            api_key = creds.get("api_key") if creds else self.get_config("api_key")
            
            if not api_key:
                return {"status": "error", "error": "JotForm API Key is required."}

            action = self.get_config("action", "get_forms")
            form_id = self.get_config("form_id") or (str(input_data) if isinstance(input_data, str) and len(input_data) > 5 else None)
            limit = int(self.get_config("limit", 10))

            base_url = "https://api.jotform.com"
            params = {"apiKey": api_key, "limit": limit}

            async with aiohttp.ClientSession() as session:
                if action == "get_forms":
                    url = f"{base_url}/user/forms"
                    async with session.get(url, params=params) as resp:
                        res_data = await resp.json()
                        content = res_data.get("content", [])
                        return {
                            "status": "success",
                            "data": {"result": content, "count": len(content)}
                        }

                elif action == "get_form_details":
                    if not form_id:
                         return {"status": "error", "error": "Form ID is required."}
                    url = f"{base_url}/form/{form_id}"
                    async with session.get(url, params=params) as resp:
                        res_data = await resp.json()
                        return {
                            "status": "success",
                            "data": {"result": res_data.get("content")}
                        }

                elif action == "get_submissions":
                    if not form_id:
                         return {"status": "error", "error": "Form ID is required."}
                    url = f"{base_url}/form/{form_id}/submissions"
                    async with session.get(url, params=params) as resp:
                        res_data = await resp.json()
                        content = res_data.get("content", [])
                        return {
                            "status": "success",
                            "data": {"result": content, "count": len(content)}
                        }

                return {"status": "error", "error": f"Unsupported action: {action}"}

        except Exception as e:
            return {"status": "error", "error": f"JotForm Node Failed: {str(e)}"}
