"""
CircleCI Node - Studio Standard (Universal Method)
Batch 96: Developer Tools (n8n Critical - The Final Push)
"""
from typing import Any, Dict, Optional, List
import aiohttp
from ..base import BaseNode
from ..registry import register_node

@register_node("circleci_node")
class CircleCINode(BaseNode):
    """
    Trigger pipelines and get project insights via CircleCI API v2.
    """
    node_type = "circleci_node"
    version = "1.0.0"
    category = "developer_tools"
    credentials_required = ["circleci_auth"]


    properties = [
        {
            'displayName': 'Operation',
            'name': 'operation',
            'type': 'options',
            'default': 'trigger_pipeline',
            'options': [
                {'name': 'Trigger Pipeline', 'value': 'trigger_pipeline'},
                {'name': 'Get Pipelines', 'value': 'get_pipelines'},
                {'name': 'Get Project Slug', 'value': 'get_project_slug'},
            ],
            'description': 'CircleCI action',
        },
        {
            'displayName': 'Branch',
            'name': 'branch',
            'type': 'string',
            'default': '',
        },
        {
            'displayName': 'Project Slug',
            'name': 'project_slug',
            'type': 'string',
            'default': '',
            'description': 'Project Slug (e.g. gh/org/repo)',
        },
    ]
    inputs = {
        "action": {
            "type": "dropdown",
            "default": "trigger_pipeline",
            "options": ["trigger_pipeline", "get_pipelines", "get_project_slug"],
            "description": "CircleCI action"
        },
        "project_slug": {
            "type": "string",
            "description": "Project Slug (e.g. gh/org/repo)"
        },
        "branch": {
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
            # 1. Authentication
            creds = await self.get_credential("circleci_auth")
            api_token = creds.get("api_token")
            
            if not api_token:
                return {"status": "error", "error": "CircleCI API Token required."}

            headers = {
                "Circle-Token": api_token,
                "Content-Type": "application/json",
                "Accept": "application/json"
            }
            
            # 2. Connect to Real API
            base_url = "https://circleci.com/api/v2"
            action = self.get_config("action", "trigger_pipeline")

            async with aiohttp.ClientSession() as session:
                if action == "trigger_pipeline":
                    slug = self.get_config("project_slug")
                    branch = self.get_config("branch")
                    
                    if not slug:
                        return {"status": "error", "error": "project_slug required"}
                    
                    url = f"{base_url}/project/{slug}/pipeline"
                    payload = {}
                    if branch:
                        payload["branch"] = branch
                        
                    async with session.post(url, headers=headers, json=payload) as resp:
                        if resp.status != 201:
                            return {"status": "error", "error": f"CircleCI API Error: {resp.status}"}
                        res_data = await resp.json()
                        return {"status": "success", "data": {"result": res_data}}

                elif action == "get_pipelines":
                    slug = self.get_config("project_slug")
                    
                    if not slug:
                         # List all pipelines
                         url = f"{base_url}/pipeline"
                    else:
                         # List project pipelines
                         url = f"{base_url}/project/{slug}/pipeline"
                    
                    async with session.get(url, headers=headers) as resp:
                        if resp.status != 200:
                            return {"status": "error", "error": f"CircleCI API Error: {resp.status}"}
                        res_data = await resp.json()
                        return {"status": "success", "data": {"result": res_data.get("items", [])}}

                return {"status": "error", "error": f"Unsupported action: {action}"}

        except Exception as e:
            return {"status": "error", "error": f"CircleCI Node Failed: {str(e)}"}