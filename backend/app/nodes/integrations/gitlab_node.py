import aiohttp
from typing import Any, Dict, Optional, List
from ..base import BaseNode
from ..registry import register_node

@register_node("gitlab_action")
class GitLabNode(BaseNode):
    """
    Automate GitLab actions (Issues, Project info).
    """
    node_type = "gitlab_action"
    version = "1.0.0"
    category = "integrations"
    credentials_required = ["gitlab_auth"]

    inputs = {
        "action": {"type": "string", "default": "create_issue", "enum": ["create_issue", "get_project_info"]},
        "project_id": {"type": "string", "description": "Numeric ID or URL-encoded path"},
        "base_url": {"type": "string", "default": "https://gitlab.com"}
    }
    outputs = {
        "id": {"type": "string"},
        "url": {"type": "string"},
        "status": {"type": "string"}
    }

    async def execute(self, input_data: Any, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        try:
            # 1. Resolve Auth
            creds = await self.get_credential("gitlab_auth")
            token = creds.get("token") or creds.get("personal_access_token") if creds else self.get_config("personal_access_token")
            base_url = self.get_config("base_url", "https://gitlab.com").rstrip('/')
            project_id = self.get_config("project_id")

            if not token or not project_id:
                return {"status": "error", "error": "GitLab Token and Project ID are required."}

            headers = {"PRIVATE-TOKEN": token, "Content-Type": "application/json"}
            action = self.get_config("action", "create_issue")

            async with aiohttp.ClientSession() as session:
                if action == "create_issue":
                    url = f"{base_url}/api/v4/projects/{project_id}/issues"
                    payload = input_data if isinstance(input_data, dict) else {"title": str(input_data)}
                    async with session.post(url, json=payload, headers=headers) as resp:
                        result = await resp.json()
                        if resp.status >= 400:
                            return {"status": "error", "error": f"GitLab Error: {result.get('message')}"}
                        return {
                            "status": "success",
                            "data": {
                                "id": result.get("iid"),
                                "url": result.get("web_url")
                            }
                        }
                elif action == "get_project_info":
                    url = f"{base_url}/api/v4/projects/{project_id}"
                    async with session.get(url, headers=headers) as resp:
                        result = await resp.json()
                        if resp.status >= 400:
                            return {"status": "error", "error": f"GitLab Error: {result.get('message')}"}
                        return {
                            "status": "success",
                            "data": result
                        }

            return {"status": "error", "error": f"Unsupported action: {action}"}

        except Exception as e:
            return {"status": "error", "error": f"GitLab Node Error: {str(e)}"}
