"""
GitHub DevOps Node - Studio Standard
Batch 45: DevOps & Infrastructure
"""
from typing import Any, Dict, Optional, List
import aiohttp
import json
import base64
from ...base import BaseNode
from ...registry import register_node

@register_node("github_devops")
class GitHubDevOpsNode(BaseNode):
    """
    Manage GitHub resources: Issues, Pull Requests, Files, and Repo Info.
    """
    node_type = "github_devops"
    version = "1.0.0"
    category = "devops"
    credentials_required = ["github_auth"]

    inputs = {
        "action": {
            "type": "dropdown",
            "default": "get_repo_info",
            "options": [
                "get_repo_info", 
                "create_issue", 
                "create_pull_request", 
                "list_repo_contents", 
                "get_file_content"
            ],
            "description": "Action to perform on GitHub"
        },
        "repo_owner": {
            "type": "string",
            "required": True,
            "description": "Owner of the repository (e.g., 'octocat')"
        },
        "repo_name": {
            "type": "string",
            "required": True,
            "description": "Name of the repository (e.g., 'Hello-World')"
        },
        "path": {
            "type": "string",
            "optional": True,
            "description": "File or directory path (for file actions)"
        },
        "data": {
            "type": "json",
            "optional": True,
            "description": "Structured data for creation (Issues/PRs)"
        }
    }

    outputs = {
        "result": {"type": "any"},
        "url": {"type": "string"},
        "id": {"type": "string"}
    }

    async def execute(self, input_data: Any, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        try:
            # 1. Resolve Auth
            creds = await self.get_credential("github_auth")
            token = None
            if creds:
                token = creds.get("token") or creds.get("personal_access_token")
            
            if not token:
                token = self.get_config("personal_access_token")

            if not token:
                return {"status": "error", "error": "GitHub Personal Access Token is required."}

            # 2. Setup API
            owner = self.get_config("repo_owner")
            repo = self.get_config("repo_name")
            action = self.get_config("action", "get_repo_info")
            base_url = f"https://api.github.com/repos/{owner}/{repo}"
            
            headers = {
                "Authorization": f"token {token}",
                "Accept": "application/vnd.github.v3+json",
                "User-Agent": "Studio-DevOps-Agent"
            }

            async with aiohttp.ClientSession() as session:
                if action == "get_repo_info":
                    async with session.get(base_url, headers=headers) as resp:
                        result = await resp.json()
                        if resp.status >= 400:
                            return {"status": "error", "error": f"GitHub API Error: {result.get('message')}"}
                        return {
                            "status": "success",
                            "data": {
                                "result": result,
                                "url": result.get("html_url")
                            }
                        }

                elif action == "create_issue":
                    url = f"{base_url}/issues"
                    payload = self.get_config("data", {})
                    if isinstance(input_data, dict):
                        payload.update(input_data)
                    elif isinstance(input_data, str) and input_data:
                        payload["title"] = input_data

                    if "title" not in payload:
                        return {"status": "error", "error": "Issue 'title' is required."}

                    async with session.post(url, json=payload, headers=headers) as resp:
                        result = await resp.json()
                        if resp.status >= 400:
                            return {"status": "error", "error": f"GitHub API Error: {result.get('message')}"}
                        return {
                            "status": "success",
                            "data": {
                                "result": result,
                                "url": result.get("html_url"),
                                "id": str(result.get("number"))
                            }
                        }

                elif action == "create_pull_request":
                    url = f"{base_url}/pulls"
                    payload = self.get_config("data", {})
                    if isinstance(input_data, dict):
                        payload.update(input_data)
                    
                    if not all(k in payload for k in ["title", "head", "base"]):
                         return {"status": "error", "error": "PR requires 'title', 'head' (branch), and 'base' (branch)."}

                    async with session.post(url, json=payload, headers=headers) as resp:
                        result = await resp.json()
                        if resp.status >= 400:
                            return {"status": "error", "error": f"GitHub API Error: {result.get('message')}"}
                        return {
                            "status": "success",
                            "data": {
                                "result": result,
                                "url": result.get("html_url"),
                                "id": str(result.get("number"))
                            }
                        }

                elif action == "list_repo_contents":
                    path = self.get_config("path", "")
                    url = f"{base_url}/contents/{path}"
                    async with session.get(url, headers=headers) as resp:
                        result = await resp.json()
                        if resp.status >= 400:
                            return {"status": "error", "error": f"GitHub API Error: {result.get('message')}"}
                        return {
                            "status": "success",
                            "data": {
                                "result": result,
                                "count": len(result) if isinstance(result, list) else 1
                            }
                        }

                elif action == "get_file_content":
                    path = self.get_config("path", "")
                    if not path:
                         return {"status": "error", "error": "File 'path' is required."}
                    
                    url = f"{base_url}/contents/{path}"
                    async with session.get(url, headers=headers) as resp:
                        result = await resp.json()
                        if resp.status >= 400:
                            return {"status": "error", "error": f"GitHub API Error: {result.get('message')}"}
                        
                        if result.get("encoding") == "base64":
                            content = base64.b64decode(result.get("content")).decode("utf-8")
                        else:
                            content = result.get("content")

                        return {
                            "status": "success",
                            "data": {
                                "result": content,
                                "metadata": {
                                    "sha": result.get("sha"),
                                    "size": result.get("size"),
                                    "url": result.get("html_url")
                                }
                            }
                        }

                return {"status": "error", "error": f"Unsupported action: {action}"}

        except Exception as e:
            return {"status": "error", "error": f"GitHub DevOps Node Failed: {str(e)}"}
