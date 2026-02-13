"""
SurveyMonkey Node - Studio Standard
Batch 57: Forms & Surveys
"""
from typing import Any, Dict, Optional, List
import aiohttp
from ...base import BaseNode
from ...registry import register_node

@register_node("surveymonkey_node")
class SurveyMonkeyNode(BaseNode):
    """
    Interact with SurveyMonkey API to retrieve surveys, questions, and responses.
    """
    node_type = "surveymonkey_node"
    version = "1.0.0"
    category = "forms"
    credentials_required = ["surveymonkey_auth"]

    inputs = {
        "action": {
            "type": "dropdown",
            "default": "list_surveys",
            "options": ["list_surveys", "get_survey_details", "get_responses", "get_survey_summary"],
            "description": "SurveyMonkey action to perform"
        },
        "survey_id": {
            "type": "string",
            "optional": True,
            "description": "Unique ID of the survey"
        },
        "page_size": {
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
            creds = await self.get_credential("surveymonkey_auth")
            access_token = creds.get("access_token") if creds else self.get_config("access_token")
            
            if not access_token:
                return {"status": "error", "error": "SurveyMonkey Access Token is required."}

            action = self.get_config("action", "list_surveys")
            survey_id = self.get_config("survey_id") or (str(input_data) if isinstance(input_data, str) and len(input_data) > 5 else None)
            page_size = int(self.get_config("page_size", 10))

            headers = {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json"
            }
            
            base_url = "https://api.surveymonkey.com/v3"

            async with aiohttp.ClientSession() as session:
                if action == "list_surveys":
                    url = f"{base_url}/surveys"
                    async with session.get(url, headers=headers) as resp:
                        res_data = await resp.json()
                        data = res_data.get("data", [])
                        return {
                            "status": "success",
                            "data": {"result": data, "count": len(data)}
                        }

                elif action == "get_survey_details":
                    if not survey_id:
                         return {"status": "error", "error": "Survey ID is required."}
                    url = f"{base_url}/surveys/{survey_id}/details"
                    async with session.get(url, headers=headers) as resp:
                        res_data = await resp.json()
                        return {
                            "status": "success",
                            "data": {"result": res_data}
                        }

                elif action == "get_responses":
                    if not survey_id:
                         return {"status": "error", "error": "Survey ID is required."}
                    # To get full responses, we usually need /surveys/{id}/responses/bulk
                    url = f"{base_url}/surveys/{survey_id}/responses/bulk"
                    async with session.get(url, headers=headers) as resp:
                        res_data = await resp.json()
                        data = res_data.get("data", [])
                        return {
                            "status": "success",
                            "data": {"result": data, "count": len(data)}
                        }

                return {"status": "error", "error": f"Unsupported SurveyMonkey action: {action}"}

        except Exception as e:
            return {"status": "error", "error": f"SurveyMonkey Node Failed: {str(e)}"}
