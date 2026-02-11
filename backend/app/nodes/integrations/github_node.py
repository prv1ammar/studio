import aiohttp
import json
from typing import Any, Dict, Optional
from pydantic import Field
from app.nodes.base import BaseNode, NodeConfig
from app.nodes.registry import register_node

class GitHubConfig(NodeConfig):
    personal_access_token: Optional[str] = Field(None, description="GitHub Personal Access Token")
    repo_owner: Optional[str] = Field(None, description="GitHub Username or Organization")
    repo_name: Optional[str] = Field(None, description="Repository Name")
    credentials_id: Optional[str] = Field(None, description="GitHub Credentials ID")
    action: str = Field("create_issue", description="Action (create_issue, get_repo_info)")

@register_node("github_node")
class GitHubNode(BaseNode):
    node_id = "github_node"
    config_model = GitHubConfig

    async def execute(self, input_data: Any, context: Optional[Dict[str, Any]] = None) -> Any:
        # 1. Auth Retrieval
        creds = await self.get_credential("credentials_id")
        token = creds.get("token") if creds else self.get_config("personal_access_token")
        owner = self.get_config("repo_owner")
        repo = self.get_config("repo_name")

        if not token or not owner or not repo:
            return {"error": "GitHub Token, Owner, and Repo Name are required."}

        action = self.get_config("action")
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
                            return {"error": f"GitHub API Error: {result.get('message')}"}
                        return {"status": "success", "issue_url": result.get("html_url"), "number": result.get("number")}

                elif action == "get_repo_info":
                    async with session.get(base_url, headers=headers) as resp:
                        result = await resp.json()
                        if resp.status >= 400:
                            return {"error": f"GitHub API Error: {result.get('message')}"}
                        return {
                            "full_name": result.get("full_name"),
                            "description": result.get("description"),
                            "stars": result.get("stargazers_count"),
                            "forks": result.get("forks_count")
                        }

                return {"error": f"Unsupported GitHub action: {action}"}

            except Exception as e:
                return {"error": f"GitHub Node Failed: {str(e)}"}
