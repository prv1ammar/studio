"""
Upwork Node - Studio Standard
Batch 74: Professional Services
"""
from typing import Any, Dict, Optional, List
import aiohttp
from ..base import BaseNode
from ..registry import register_node

@register_node("upwork_node")
class UpworkNode(BaseNode):
    """
    Automate job postings and talent discovery via Upwork API.
    """
    node_type = "upwork_node"
    version = "1.0.0"
    category = "professional_services"
    credentials_required = ["upwork_auth"]


    properties = [
        {
            'displayName': 'Operation',
            'name': 'operation',
            'type': 'options',
            'default': 'search_jobs',
            'options': [
                {'name': 'Search Jobs', 'value': 'search_jobs'},
                {'name': 'Get User Info', 'value': 'get_user_info'},
                {'name': 'List Teams', 'value': 'list_teams'},
                {'name': 'Get Job Details', 'value': 'get_job_details'},
            ],
            'description': 'Upwork action',
        },
        {
            'displayName': 'Job Key',
            'name': 'job_key',
            'type': 'string',
            'default': '',
            'description': 'ID/Key of the job',
        },
        {
            'displayName': 'Query',
            'name': 'query',
            'type': 'string',
            'default': '',
            'description': 'Search query for jobs',
        },
    ]
    inputs = {
        "action": {
            "type": "dropdown",
            "default": "search_jobs",
            "options": ["search_jobs", "get_user_info", "list_teams", "get_job_details"],
            "description": "Upwork action"
        },
        "query": {
            "type": "string",
            "optional": True,
            "description": "Search query for jobs"
        },
        "job_key": {
            "type": "string",
            "optional": True,
            "description": "ID/Key of the job"
        }
    }

    outputs = {
        "result": {"type": "any"},
        "status": {"type": "string"},
        "count": {"type": "number"}
    }

    async def execute(self, input_data: Any, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        try:
            creds = await self.get_credential("upwork_auth")
            access_token = creds.get("access_token") if creds else self.get_config("access_token")
            
            if not access_token:
                return {"status": "error", "error": "Upwork OAuth Access Token is required."}

            headers = {
                "Authorization": f"Bearer {access_token}",
                "Accept": "application/json"
            }
            
            base_url = "https://www.upwork.com/api"
            action = self.get_config("action", "search_jobs")

            async with aiohttp.ClientSession() as session:
                if action == "get_user_info":
                    url = f"{base_url}/auth/v1/info.json"
                    async with session.get(url, headers=headers) as resp:
                        res_data = await resp.json()
                        return {"status": "success", "data": {"result": res_data.get("info")}}

                elif action == "search_jobs":
                    query = self.get_config("query") or str(input_data)
                    # Note: Upwork Job Search API v2
                    url = f"{base_url}/profiles/v2/search/jobs.json"
                    params = {"q": query}
                    async with session.get(url, headers=headers, params=params) as resp:
                        res_data = await resp.json()
                        jobs = res_data.get("jobs", [])
                        return {"status": "success", "data": {"result": jobs, "count": len(jobs)}}

                elif action == "list_teams":
                    url = f"{base_url}/hr/v2/teams.json"
                    async with session.get(url, headers=headers) as resp:
                        res_data = await resp.json()
                        teams = res_data.get("teams", [])
                        return {"status": "success", "data": {"result": teams, "count": len(teams)}}

                return {"status": "error", "error": f"Unsupported action: {action}"}

        except Exception as e:
            return {"status": "error", "error": f"Upwork Node Failed: {str(e)}"}