"""
GitHub Node - Studio Standard (Universal Method)
Batch 96: Developer Tools (n8n Critical)
"""
from typing import Any, Dict, Optional, List
import aiohttp
from ...base import BaseNode
from ...registry import register_node

@register_node("github_node")
class GitHubNode(BaseNode):
    """
    Manage repositories, issues, and pull requests via GitHub API v3.
    """
    node_type = "github_node"
    version = "1.0.0"
    category = "developer_tools"
    credentials_required = ["github_auth"]

    inputs = {
        "action": {
            "type": "dropdown",
            "default": "get_repository",
            "options": ["get_repository", "list_issues", "create_issue", "list_pull_requests", "get_user"],
            "description": "GitHub action"
        },
        "owner": {
            "type": "string",
            "description": "Owner of the repository"
        },
        "repo": {
            "type": "string",
            "description": "Repository name"
        },
        "title": {
            "type": "string",
            "optional": True,
            "description": "Title for issue/PR"
        },
        "body": {
            "type": "string",
            "optional": True,
            "description": "Body content"
        }
    }

    outputs = {
        "result": {"type": "any"},
        "status": {"type": "string"}
    }

    async def execute(self, input_data: Any, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        try:
            # 1. Authentication
            creds = await self.get_credential("github_auth")
            access_token = creds.get("access_token")
            
            if not access_token:
                return {"status": "error", "error": "GitHub Access Token required."}

            headers = {
                "Authorization": f"Bearer {access_token}",
                "Accept": "application/vnd.github.v3+json",
                "User-Agent": "Studio-App"
            }
            
            # 2. Connect to Real API
            base_url = "https://api.github.com"
            action = self.get_config("action", "get_repository")

            async with aiohttp.ClientSession() as session:
                if action == "get_user":
                    url = f"{base_url}/user"
                    async with session.get(url, headers=headers) as resp:
                        if resp.status != 200:
                            return {"status": "error", "error": f"GitHub API Error: {resp.status}"}
                        res_data = await resp.json()
                        return {"status": "success", "data": {"result": res_data}}

                # Repository based actions
                owner = self.get_config("owner")
                repo = self.get_config("repo")
                
                if not owner or not repo:
                    return {"status": "error", "error": "owner and repo required"}

                if action == "get_repository":
                    url = f"{base_url}/repos/{owner}/{repo}"
                    async with session.get(url, headers=headers) as resp:
                        if resp.status != 200:
                            return {"status": "error", "error": f"GitHub API Error: {resp.status}"}
                        res_data = await resp.json()
                        return {"status": "success", "data": {"result": res_data}}

                elif action == "list_issues":
                    url = f"{base_url}/repos/{owner}/{repo}/issues"
                    async with session.get(url, headers=headers) as resp:
                        if resp.status != 200:
                            return {"status": "error", "error": f"GitHub API Error: {resp.status}"}
                        res_data = await resp.json()
                        return {"status": "success", "data": {"result": res_data}}

                elif action == "create_issue":
                    title = self.get_config("title") or str(input_data)
                    body = self.get_config("body", "")
                    
                    if not title:
                        return {"status": "error", "error": "title required for issue"}
                    
                    url = f"{base_url}/repos/{owner}/{repo}/issues"
                    payload = {"title": title, "body": body}
                    async with session.post(url, headers=headers, json=payload) as resp:
                        if resp.status != 201:
                            return {"status": "error", "error": f"GitHub API Error: {resp.status}"}
                        res_data = await resp.json()
                        return {"status": "success", "data": {"result": res_data}}

                elif action == "list_pull_requests":
                    url = f"{base_url}/repos/{owner}/{repo}/pulls"
                    async with session.get(url, headers=headers) as resp:
                        if resp.status != 200:
                            return {"status": "error", "error": f"GitHub API Error: {resp.status}"}
                        res_data = await resp.json()
                        return {"status": "success", "data": {"result": res_data}}

                return {"status": "error", "error": f"Unsupported action: {action}"}

        except Exception as e:
            return {"status": "error", "error": f"GitHub Node Failed: {str(e)}"}
