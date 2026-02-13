"""
GitLab Node - Studio Standard (Universal Method)
Batch 96: Developer Tools (n8n Critical)
"""
from typing import Any, Dict, Optional, List
import aiohttp
from ...base import BaseNode
from ...registry import register_node

@register_node("gitlab_node")
class GitLabNode(BaseNode):
    """
    Manage projects, issues, and pipelines via GitLab API v4.
    """
    node_type = "gitlab_node"
    version = "1.0.0"
    category = "developer_tools"
    credentials_required = ["gitlab_auth"]

    inputs = {
        "action": {
            "type": "dropdown",
            "default": "list_projects",
            "options": ["list_projects", "get_project", "list_issues", "trigger_pipeline"],
            "description": "GitLab action"
        },
        "project_id": {
            "type": "string",
            "optional": True,
            "description": "Project ID or URL-encoded path"
        },
        "ref": {
            "type": "string",
            "default": "main",
            "description": "Branch or tag for pipeline trigger"
        }
    }

    outputs = {
        "result": {"type": "any"},
        "status": {"type": "string"}
    }

    async def execute(self, input_data: Any, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        try:
            # 1. Authentication
            creds = await self.get_credential("gitlab_auth")
            access_token = creds.get("access_token")
            host = creds.get("host", "gitlab.com")
            
            if not access_token:
                return {"status": "error", "error": "GitLab Access Token required."}

            headers = {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json"
            }
            
            # 2. Connect to Real API
            base_url = f"https://{host}/api/v4"
            action = self.get_config("action", "list_projects")

            async with aiohttp.ClientSession() as session:
                if action == "list_projects":
                    url = f"{base_url}/projects"
                    params = {"membership": "true", "per_page": 20}
                    async with session.get(url, headers=headers, params=params) as resp:
                        if resp.status != 200:
                            return {"status": "error", "error": f"GitLab API Error: {resp.status}"}
                        res_data = await resp.json()
                        return {"status": "success", "data": {"result": res_data}}

                elif action == "get_project":
                    project_id = self.get_config("project_id")
                    if not project_id:
                        return {"status": "error", "error": "project_id required"}
                    
                    # URL encode path if needed (simple check)
                    if "/" in project_id:
                        import urllib.parse
                        project_id = urllib.parse.quote(project_id, safe='')
                    
                    url = f"{base_url}/projects/{project_id}"
                    async with session.get(url, headers=headers) as resp:
                        if resp.status != 200:
                            return {"status": "error", "error": f"GitLab API Error: {resp.status}"}
                        res_data = await resp.json()
                        return {"status": "success", "data": {"result": res_data}}

                elif action == "list_issues":
                    project_id = self.get_config("project_id")
                    if not project_id:
                        return {"status": "error", "error": "project_id required"}
                    
                    if "/" in project_id:
                        import urllib.parse
                        project_id = urllib.parse.quote(project_id, safe='')

                    url = f"{base_url}/projects/{project_id}/issues"
                    async with session.get(url, headers=headers) as resp:
                        if resp.status != 200:
                            return {"status": "error", "error": f"GitLab API Error: {resp.status}"}
                        res_data = await resp.json()
                        return {"status": "success", "data": {"result": res_data}}

                elif action == "trigger_pipeline":
                    project_id = self.get_config("project_id")
                    ref = self.get_config("ref", "main")
                    
                    if not project_id:
                        return {"status": "error", "error": "project_id required"}
                    
                    if "/" in project_id:
                        import urllib.parse
                        project_id = urllib.parse.quote(project_id, safe='')

                    url = f"{base_url}/projects/{project_id}/pipeline"
                    params = {"ref": ref}
                    async with session.post(url, headers=headers, params=params) as resp:
                        if resp.status != 201:
                            return {"status": "error", "error": f"GitLab API Error: {resp.status}"}
                        res_data = await resp.json()
                        return {"status": "success", "data": {"result": res_data}}

                return {"status": "error", "error": f"Unsupported action: {action}"}

        except Exception as e:
            return {"status": "error", "error": f"GitLab Node Failed: {str(e)}"}
