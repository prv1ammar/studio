"""
Bitbucket Node - Studio Standard (Universal Method)
Batch 96: Developer Tools (n8n Critical)
"""
from typing import Any, Dict, Optional, List
import aiohttp
from ...base import BaseNode
from ...registry import register_node

@register_node("bitbucket_node")
class BitbucketNode(BaseNode):
    """
    Manage repositories and pull requests via Bitbucket Cloud API v2.
    """
    node_type = "bitbucket_node"
    version = "1.0.0"
    category = "developer_tools"
    credentials_required = ["bitbucket_auth"]

    inputs = {
        "action": {
            "type": "dropdown",
            "default": "list_repositories",
            "options": ["list_repositories", "get_repository", "list_pull_requests"],
            "description": "Bitbucket action"
        },
        "workspace": {
            "type": "string",
            "description": "Workspace ID or slug"
        },
        "repo_slug": {
            "type": "string",
            "optional": True,
            "description": "Repository slug"
        }
    }

    outputs = {
        "result": {"type": "any"},
        "status": {"type": "string"}
    }

    async def execute(self, input_data: Any, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        try:
            # 1. Authentication
            creds = await self.get_credential("bitbucket_auth")
            # Can be Basic Auth (app password) or OAuth
            username = creds.get("username")
            app_password = creds.get("app_password")
            access_token = creds.get("access_token")
            
            headers = {"Content-Type": "application/json"}
            auth = None
            
            if access_token:
                headers["Authorization"] = f"Bearer {access_token}"
            elif username and app_password:
                auth = aiohttp.BasicAuth(username, app_password)
            else:
                 return {"status": "error", "error": "Bitbucket Auth required (Token or User/AppPass)."}
            
            # 2. Connect to Real API
            base_url = "https://api.bitbucket.org/2.0"
            action = self.get_config("action", "list_repositories")
            workspace = self.get_config("workspace")

            if not workspace:
                return {"status": "error", "error": "workspace required"}

            async with aiohttp.ClientSession(auth=auth) as session:
                if action == "list_repositories":
                    url = f"{base_url}/repositories/{workspace}"
                    async with session.get(url, headers=headers) as resp:
                        if resp.status != 200:
                            return {"status": "error", "error": f"Bitbucket API Error: {resp.status}"}
                        res_data = await resp.json()
                        return {"status": "success", "data": {"result": res_data.get("values", [])}}

                elif action == "get_repository":
                    repo_slug = self.get_config("repo_slug")
                    if not repo_slug:
                        return {"status": "error", "error": "repo_slug required"}
                    
                    url = f"{base_url}/repositories/{workspace}/{repo_slug}"
                    async with session.get(url, headers=headers) as resp:
                        if resp.status != 200:
                            return {"status": "error", "error": f"Bitbucket API Error: {resp.status}"}
                        res_data = await resp.json()
                        return {"status": "success", "data": {"result": res_data}}

                elif action == "list_pull_requests":
                    repo_slug = self.get_config("repo_slug")
                    if not repo_slug:
                        return {"status": "error", "error": "repo_slug required"}
                    
                    url = f"{base_url}/repositories/{workspace}/{repo_slug}/pullrequests"
                    async with session.get(url, headers=headers) as resp:
                        if resp.status != 200:
                            return {"status": "error", "error": f"Bitbucket API Error: {resp.status}"}
                        res_data = await resp.json()
                        return {"status": "success", "data": {"result": res_data.get("values", [])}}

                return {"status": "error", "error": f"Unsupported action: {action}"}

        except Exception as e:
            return {"status": "error", "error": f"Bitbucket Node Failed: {str(e)}"}
