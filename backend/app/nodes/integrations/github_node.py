import aiohttp
import json
from typing import Any, Dict, Optional
from ..base import BaseNode
from ..registry import register_node

@register_node("github_action")
class GitHubNode(BaseNode):
    """Integrates with GitHub API for issues and repo management."""
    node_type = "github_action"
    version = "1.0.0"
    category = "integrations"
    credentials_required = ["github_auth"]

    inputs = {
        "action": {"type": "string", "enum": ["create_issue", "get_repo_info"], "default": "create_issue"},
        "repo_owner": {"type": "string", "description": "Owner of the repository"},
        "repo_name": {"type": "string", "description": "Repository name"},
        "data": {"type": "any", "description": "Input for the action (e.g. issue title/body)"}
    }
    outputs = {
        "result": {"type": "object"},
        "status": {"type": "string"}
    }

    async def execute(self, input_data: Any, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        # 1. Auth Retrieval
        creds = await self.get_credential("github_auth")
        token = creds.get("token") or creds.get("personal_access_token") if creds else self.get_config("personal_access_token")
        owner = self.get_config("repo_owner")
        repo = self.get_config("repo_name")

        if not token or not owner or not repo:
            return {"status": "error", "error": "GitHub Token, Owner, and Repo Name are required.", "data": None}

        action = self.get_config("action", "create_issue")
        base_url = f"https://api.github.com/repos/{owner}/{repo}"
        headers = {
            "Authorization": f"token {token}",
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "Studio-Automation-Agent"
        }

        async with aiohttp.ClientSession() as session:
            try:
                if action == "create_issue":
                    url = f"{base_url}/issues"
                    payload = input_data if isinstance(input_data, dict) else {"title": str(input_data)}
                    async with session.post(url, json=payload, headers=headers) as resp:
                        result = await resp.json()
                        if resp.status >= 400:
                            return {"status": "error", "error": f"GitHub API Error: {result.get('message')}", "data": result}
                        return {
                            "status": "success", 
                            "data": {
                                "issue_url": result.get("html_url"), 
                                "number": result.get("number"),
                                "id": result.get("id")
                            }
                        }

                elif action == "get_repo_info":
                    async with session.get(base_url, headers=headers) as resp:
                        result = await resp.json()
                        if resp.status >= 400:
                            return {"status": "error", "error": f"GitHub API Error: {result.get('message')}", "data": result}
                        return {
                            "status": "success",
                            "data": {
                                "full_name": result.get("full_name"),
                                "description": result.get("description"),
                                "stars": result.get("stargazers_count"),
                                "forks": result.get("forks_count")
                            }
                        }

                return {"status": "error", "error": f"Unsupported GitHub action: {action}", "data": None}

            except Exception as e:
                return {"status": "error", "error": f"GitHub Node Failed: {str(e)}", "data": None}
