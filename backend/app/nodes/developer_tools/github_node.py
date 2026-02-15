"""
GitHub Node - Studio Standard (Universal Method)
Batch 110: Developer Tools & Databases
"""
from typing import Any, Dict, Optional
import aiohttp
from ...base import BaseNode
from ...registry import register_node

@register_node("github_node")
class GitHubNode(BaseNode):
    """
    GitHub integration for version control.
    """
    node_type = "github_node"
    version = "1.0.0"
    category = "developer_tools"
    credentials_required = ["github_auth"]

    inputs = {
        "action": {
            "type": "dropdown",
            "default": "create_issue",
            "options": ["create_issue", "list_issues", "create_pr", "list_repos"],
            "description": "GitHub action"
        },
        "owner": {
            "type": "string",
            "optional": True
        },
        "repo": {
            "type": "string",
            "optional": True
        },
        "title": {
            "type": "string",
            "optional": True
        },
        "body": {
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
            creds = await self.get_credential("github_auth")
            access_token = creds.get("access_token") # or pat
            base_url = "https://api.github.com"
            headers = {
                "Authorization": f"Bearer {access_token}",
                "Accept": "application/vnd.github+json"
            }
            
            if not access_token:
                return {"status": "error", "error": "GitHub access token required"}

            action = self.get_config("action", "create_issue")

            async with aiohttp.ClientSession() as session:
                if action == "create_issue":
                    owner = self.get_config("owner")
                    repo = self.get_config("repo")
                    title = self.get_config("title")
                    body = self.get_config("body", "")
                    
                    if not owner or not repo or not title:
                        return {"status": "error", "error": "owner, repo, and title required"}
                        
                    payload = {"title": title, "body": body}
                    
                    url = f"{base_url}/repos/{owner}/{repo}/issues"
                    async with session.post(url, headers=headers, json=payload) as resp:
                         if resp.status != 201:
                            error_text = await resp.text()
                            return {"status": "error", "error": f"GitHub API Error {resp.status}: {error_text}"}
                         res_data = await resp.json()
                         return {"status": "success", "data": {"result": res_data}}
                
                elif action == "list_issues":
                    owner = self.get_config("owner")
                    repo = self.get_config("repo")
                    if not owner or not repo: return {"status": "error", "error": "owner and repo required"}
                    
                    url = f"{base_url}/repos/{owner}/{repo}/issues"
                    async with session.get(url, headers=headers) as resp:
                         res_data = await resp.json()
                         return {"status": "success", "data": {"result": res_data}}

                elif action == "list_repos":
                    url = f"{base_url}/user/repos"
                    async with session.get(url, headers=headers) as resp:
                         res_data = await resp.json()
                         return {"status": "success", "data": {"result": res_data}}

            return {"status": "error", "error": f"Unsupported action: {action}"}

        except Exception as e:
            return {"status": "error", "error": f"GitHub Node Failed: {str(e)}"}
