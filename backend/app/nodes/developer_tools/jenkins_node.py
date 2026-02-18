"""
Jenkins Node - Studio Standard (Universal Method)
Batch 96: Developer Tools (n8n Critical)
"""
from typing import Any, Dict, Optional, List
import aiohttp
from ..base import BaseNode
from ..registry import register_node

@register_node("jenkins_node")
class JenkinsNode(BaseNode):
    """
    Trigger builds and get job status via Jenkins REST API.
    """
    node_type = "jenkins_node"
    version = "1.0.0"
    category = "developer_tools"
    credentials_required = ["jenkins_auth"]


    properties = [
        {
            'displayName': 'Operation',
            'name': 'operation',
            'type': 'options',
            'default': 'trigger_build',
            'options': [
                {'name': 'Trigger Build', 'value': 'trigger_build'},
                {'name': 'Get Job Info', 'value': 'get_job_info'},
                {'name': 'Get Build Info', 'value': 'get_build_info'},
                {'name': 'Get Last Build', 'value': 'get_last_build'},
            ],
            'description': 'Jenkins action',
        },
        {
            'displayName': 'Base Url',
            'name': 'base_url',
            'type': 'string',
            'default': '',
            'description': 'Jenkins Server URL (e.g. http://jenkins.example.com)',
        },
        {
            'displayName': 'Build Number',
            'name': 'build_number',
            'type': 'string',
            'default': '',
            'description': 'Build number',
        },
        {
            'displayName': 'Job Name',
            'name': 'job_name',
            'type': 'string',
            'default': '',
            'description': 'Name of the job',
        },
    ]
    inputs = {
        "action": {
            "type": "dropdown",
            "default": "trigger_build",
            "options": ["trigger_build", "get_job_info", "get_build_info", "get_last_build"],
            "description": "Jenkins action"
        },
        "base_url": {
            "type": "string",
            "description": "Jenkins Server URL (e.g. http://jenkins.example.com)"
        },
        "job_name": {
            "type": "string",
            "description": "Name of the job"
        },
        "build_number": {
            "type": "string",
            "optional": True,
            "description": "Build number"
        }
    }

    outputs = {
        "result": {"type": "any"},
        "status": {"type": "string"}
    }

    async def execute(self, input_data: Any, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        try:
            # 1. Authentication
            creds = await self.get_credential("jenkins_auth")
            username = creds.get("username")
            api_token = creds.get("api_token")
            
            if not username or not api_token:
                return {"status": "error", "error": "Jenkins Username and API Token required."}

            auth = aiohttp.BasicAuth(username, api_token)
            
            # 2. Connect to Real API
            base_url = self.get_config("base_url", "").rstrip("/")
            if not base_url:
                 # Attempt to get from creds if stored there
                 base_url = creds.get("base_url", "").rstrip("/")
            
            if not base_url:
                return {"status": "error", "error": "Jenkins Base URL required."}

            job_name = self.get_config("job_name")
            if not job_name:
                return {"status": "error", "error": "job_name required"}

            action = self.get_config("action", "trigger_build")

            async with aiohttp.ClientSession(auth=auth) as session:
                if action == "trigger_build":
                    url = f"{base_url}/job/{job_name}/build"
                    # POST to trigger
                    async with session.post(url) as resp:
                        if resp.status not in [200, 201]:
                            return {"status": "error", "error": f"Jenkins API Error: {resp.status}"}
                        return {"status": "success", "data": {"result": {"message": f"Build triggered for {job_name}"}}}

                elif action == "get_job_info":
                    url = f"{base_url}/job/{job_name}/api/json"
                    async with session.get(url) as resp:
                        if resp.status != 200:
                            return {"status": "error", "error": f"Jenkins API Error: {resp.status}"}
                        res_data = await resp.json()
                        return {"status": "success", "data": {"result": res_data}}

                elif action == "get_build_info":
                    build_number = self.get_config("build_number")
                    if not build_number:
                        return {"status": "error", "error": "build_number required"}
                    
                    url = f"{base_url}/job/{job_name}/{build_number}/api/json"
                    async with session.get(url) as resp:
                        if resp.status != 200:
                            return {"status": "error", "error": f"Jenkins API Error: {resp.status}"}
                        res_data = await resp.json()
                        return {"status": "success", "data": {"result": res_data}}

                elif action == "get_last_build":
                    url = f"{base_url}/job/{job_name}/lastBuild/api/json"
                    async with session.get(url) as resp:
                        if resp.status != 200:
                            return {"status": "error", "error": f"Jenkins API Error: {resp.status}"}
                        res_data = await resp.json()
                        return {"status": "success", "data": {"result": res_data}}

                return {"status": "error", "error": f"Unsupported action: {action}"}

        except Exception as e:
            return {"status": "error", "error": f"Jenkins Node Failed: {str(e)}"}