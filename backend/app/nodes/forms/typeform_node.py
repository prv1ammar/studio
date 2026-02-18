"""
Typeform Node - Studio Standard
Batch 57: Forms & Surveys
"""
from typing import Any, Dict, Optional, List
import aiohttp
from ..base import BaseNode
from ..registry import register_node

@register_node("typeform_node")
class TypeformNode(BaseNode):
    """
    Interact with Typeform API to retrieve form responses and details.
    """
    node_type = "typeform_node"
    version = "1.0.0"
    category = "forms"
    credentials_required = ["typeform_auth"]


    properties = [
        {
            'displayName': 'Operation',
            'name': 'operation',
            'type': 'options',
            'default': 'list_responses',
            'options': [
                {'name': 'List Forms', 'value': 'list_forms'},
                {'name': 'Get Form', 'value': 'get_form'},
                {'name': 'List Responses', 'value': 'list_responses'},
                {'name': 'Get Latest Response', 'value': 'get_latest_response'},
            ],
            'description': 'Typeform action to perform',
        },
        {
            'displayName': 'Form Id',
            'name': 'form_id',
            'type': 'string',
            'default': '',
            'description': 'Unique ID of the form',
        },
        {
            'displayName': 'Page Size',
            'name': 'page_size',
            'type': 'string',
            'default': 10,
            'description': 'Number of results to return',
        },
        {
            'displayName': 'Since',
            'name': 'since',
            'type': 'string',
            'default': '',
            'description': 'ISO 8601 date string to filter responses',
        },
    ]
    inputs = {
        "action": {
            "type": "dropdown",
            "default": "list_responses",
            "options": ["list_forms", "get_form", "list_responses", "get_latest_response"],
            "description": "Typeform action to perform"
        },
        "form_id": {
            "type": "string",
            "optional": True,
            "description": "Unique ID of the form"
        },
        "page_size": {
            "type": "number",
            "default": 10,
            "description": "Number of results to return"
        },
        "since": {
            "type": "string",
            "optional": True,
            "description": "ISO 8601 date string to filter responses"
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
            creds = await self.get_credential("typeform_auth")
            api_key = creds.get("api_key") if creds else self.get_config("api_key")
            
            if not api_key:
                return {"status": "error", "error": "Typeform Personal Access Token is required."}

            action = self.get_config("action", "list_responses")
            form_id = self.get_config("form_id") or (str(input_data) if isinstance(input_data, str) and len(input_data) > 5 else None)
            page_size = int(self.get_config("page_size", 10))
            since = self.get_config("since")

            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            }
            
            base_url = "https://api.typeform.com"

            async with aiohttp.ClientSession() as session:
                if action == "list_forms":
                    url = f"{base_url}/forms"
                    params = {"page_size": page_size}
                    async with session.get(url, headers=headers, params=params) as resp:
                        res_data = await resp.json()
                        items = res_data.get("items", [])
                        return {
                            "status": "success",
                            "data": {"result": items, "count": len(items)}
                        }

                elif action == "get_form":
                    if not form_id:
                         return {"status": "error", "error": "Form ID is required."}
                    url = f"{base_url}/forms/{form_id}"
                    async with session.get(url, headers=headers) as resp:
                        res_data = await resp.json()
                        return {
                            "status": "success",
                            "data": {"result": res_data}
                        }

                elif action == "list_responses":
                    if not form_id:
                         return {"status": "error", "error": "Form ID is required for responses."}
                    url = f"{base_url}/forms/{form_id}/responses"
                    params = {"page_size": page_size}
                    if since:
                        params["since"] = since
                    
                    async with session.get(url, headers=headers, params=params) as resp:
                        res_data = await resp.json()
                        items = res_data.get("items", [])
                        return {
                            "status": "success",
                            "data": {"result": items, "count": len(items)}
                        }

                elif action == "get_latest_response":
                    if not form_id:
                         return {"status": "error", "error": "Form ID is required."}
                    url = f"{base_url}/forms/{form_id}/responses"
                    params = {"page_size": 1}
                    async with session.get(url, headers=headers, params=params) as resp:
                        res_data = await resp.json()
                        items = res_data.get("items", [])
                        latest = items[0] if items else None
                        return {
                            "status": "success",
                            "data": {"result": latest, "status": "fetched" if latest else "no_responses"}
                        }

                return {"status": "error", "error": f"Unsupported action: {action}"}

        except Exception as e:
            return {"status": "error", "error": f"Typeform Node Failed: {str(e)}"}