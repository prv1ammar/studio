import aiohttp
import json
from typing import Any, Dict, Optional
from pydantic import Field
from app.nodes.base import BaseNode, NodeConfig
from app.nodes.registry import register_node

class GitLabConfig(NodeConfig):
    personal_access_token: Optional[str] = Field(None, description="GitLab Private Access Token")
    base_url: str = Field("https://gitlab.com", description="GitLab Instance URL")
    project_id: Optional[str] = Field(None, description="GitLab Project ID (Numeric or URL-encoded path)")
    credentials_id: Optional[str] = Field(None, description="GitLab Credentials ID")
    action: str = Field("create_issue", description="Action (create_issue, get_project_info)")

@register_node("gitlab_node")
class GitLabNode(BaseNode):
    node_id = "gitlab_node"
    config_model = GitLabConfig

    async def execute(self, input_data: Any, context: Optional[Dict[str, Any]] = None) -> Any:
        # 1. Auth Retrieval
        creds = await self.get_credential("credentials_id")
        token = creds.get("token") if creds else self.get_config("personal_access_token")
        base_url = self.get_config("base_url").rstrip('/')
        project_id = self.get_config("project_id")

        if not token or not project_id:
            return {"error": "GitLab Token and Project ID are required."}

        action = self.get_config("action")
        headers = {
            "PRIVATE-TOKEN": token,
            "Content-Type": "application/json"
        }

        async with aiohttp.ClientSession() as session:
            try:
                if action == "create_issue":
                    url = f"{base_url}/api/v4/projects/{project_id}/issues"
                    payload = input_data if isinstance(input_data, dict) else {"title": str(input_data)}
                    async with session.post(url, json=payload, headers=headers) as resp:
                        result = await resp.json()
                        if resp.status >= 400:
                            return {"error": f"GitLab API Error: {result.get('message')}"}
                        return {"status": "success", "issue_url": result.get("web_url"), "iid": result.get("iid")}

                elif action == "get_project_info":
                    url = f"{base_url}/api/v4/projects/{project_id}"
                    async with session.get(url, headers=headers) as resp:
                        result = await resp.json()
                        if resp.status >= 400:
                            return {"error": f"GitLab API Error: {result.get('message')}"}
                        return {
                            "name": result.get("name"),
                            "description": result.get("description"),
                            "star_count": result.get("star_count"),
                            "forks_count": result.get("forks_count"),
                            "web_url": result.get("web_url")
                        }

                return {"error": f"Unsupported GitLab action: {action}"}

            except Exception as e:
                return {"error": f"GitLab Node Failed: {str(e)}"}
