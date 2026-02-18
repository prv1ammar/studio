"""
GitHub Integration Node - Studio Standard
Part of Phase 6: Rewriting Existing Nodes to remove Composio
"""
import json
import httpx
from typing import Any, Dict, Optional, List
from ..base import BaseNode
from ..registry import register_node

@register_node("github_node")
class GitHubNode(BaseNode):
    """
    Interact with GitHub repositories, issues, and pull requests directly via GitHub REST API.
    Replaces Composio GitHub implementation.
    """
    node_type = "github_node"
    version = "1.0.0"
    category = "productivity"
    credentials_required = ["github_auth"]


    properties = [
        {
            'displayName': 'Operation',
            'name': 'operation',
            'type': 'options',
            'default': 'get_repository',
            'options': [
                {'name': 'Get Repository', 'value': 'get_repository'},
                {'name': 'List Issues', 'value': 'list_issues'},
                {'name': 'Create Issue', 'value': 'create_issue'},
                {'name': 'List Pull Requests', 'value': 'list_pull_requests'},
                {'name': 'Create Pull Request', 'value': 'create_pull_request'},
                {'name': 'Get Contents', 'value': 'get_contents'},
            ],
            'description': 'Action to perform',
        },
        {
            'displayName': 'Base Branch',
            'name': 'base_branch',
            'type': 'string',
            'default': 'main',
            'description': 'Base branch for PRs',
        },
        {
            'displayName': 'Body',
            'name': 'body',
            'type': 'string',
            'default': '',
            'description': 'Body content for Issue or PR',
        },
        {
            'displayName': 'Head Branch',
            'name': 'head_branch',
            'type': 'string',
            'default': '',
            'description': 'Head branch for PRs',
        },
        {
            'displayName': 'Issue Number',
            'name': 'issue_number',
            'type': 'string',
            'default': '',
            'description': 'Issue or Pull Request number',
        },
        {
            'displayName': 'Path',
            'name': 'path',
            'type': 'string',
            'default': '',
            'description': 'File path (for get_contents)',
        },
        {
            'displayName': 'Repository',
            'name': 'repository',
            'type': 'string',
            'default': '',
            'description': 'Full repository name (e.g., owner/repo)',
            'required': True,
        },
        {
            'displayName': 'Title',
            'name': 'title',
            'type': 'string',
            'default': '',
            'description': 'Title for Issue or PR',
        },
    ]
    inputs = {
        "action": {
            "type": "dropdown",
            "default": "get_repository",
            "options": [
                "get_repository",
                "list_issues",
                "create_issue",
                "list_pull_requests",
                "create_pull_request",
                "get_contents"
            ],
            "description": "Action to perform"
        },
        "repository": {
            "type": "string",
            "required": True,
            "description": "Full repository name (e.g., owner/repo)"
        },
        "issue_number": {
            "type": "number",
            "optional": True,
            "description": "Issue or Pull Request number"
        },
        "title": {
            "type": "string",
            "optional": True,
            "description": "Title for Issue or PR"
        },
        "body": {
            "type": "string",
            "optional": True,
            "description": "Body content for Issue or PR"
        },
        "path": {
            "type": "string",
            "optional": True,
            "description": "File path (for get_contents)"
        },
        "base_branch": {
            "type": "string",
            "default": "main",
            "description": "Base branch for PRs"
        },
        "head_branch": {
            "type": "string",
            "description": "Head branch for PRs"
        }
    }

    outputs = {
        "result": {"type": "json"},
        "id": {"type": "number"},
        "url": {"type": "string"},
        "status": {"type": "string"}
    }

    async def execute(self, input_data: Any, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        try:
            # 1. Get Credentials
            creds = await self.get_credential("github_auth")
            token = None
            if creds:
                token = creds.get("token") or creds.get("api_key") or creds.get("access_token")
            
            # Fallback to config for manual API key input
            if not token:
                token = self.get_config("api_key")
            
            if not token:
                return {"status": "error", "error": "GitHub Personal Access Token is required. Please provide it via 'github_auth' credential or 'api_key' config."}

            # 2. Setup Client
            headers = {
                "Authorization": f"token {token}",
                "Accept": "application/vnd.github.v3+json",
                "User-Agent": "Studio-AI-Agent"
            }
            
            action = self.get_config("action", "get_repository")
            repo = self.get_config("repository")
            
            if not repo:
                return {"status": "error", "error": "Repository (owner/repo) is required."}

            async with httpx.AsyncClient(headers=headers, timeout=30.0) as client:
                base_api_url = f"https://api.github.com/repos/{repo}"
                
                result_data = {}
                
                if action == "get_repository":
                    resp = await client.get(base_api_url)
                    resp.raise_for_status()
                    result_data = resp.json()

                elif action == "list_issues":
                    resp = await client.get(f"{base_api_url}/issues")
                    resp.raise_for_status()
                    issues = resp.json()
                    result_data = {"issues": issues, "count": len(issues)}

                elif action == "create_issue":
                    # Use title from config or input_data
                    title = self.get_config("title")
                    if not title and isinstance(input_data, str):
                        title = input_data
                    if not title:
                        title = "New Issue from Studio"
                        
                    body = self.get_config("body") or ""
                    
                    payload = {"title": title, "body": body}
                    resp = await client.post(f"{base_api_url}/issues", json=payload)
                    resp.raise_for_status()
                    result_data = resp.json()

                elif action == "list_pull_requests":
                    resp = await client.get(f"{base_api_url}/pulls")
                    resp.raise_for_status()
                    pulls = resp.json()
                    result_data = {"pulls": pulls, "count": len(pulls)}

                elif action == "create_pull_request":
                    title = self.get_config("title") or "New Pull Request from Studio"
                    body = self.get_config("body") or ""
                    head = self.get_config("head_branch")
                    base = self.get_config("base_branch", "main")
                    
                    if not head:
                         return {"status": "error", "error": "Head branch is required for creating a PR."}
                    
                    payload = {"title": title, "body": body, "head": head, "base": base}
                    resp = await client.post(f"{base_api_url}/pulls", json=payload)
                    resp.raise_for_status()
                    result_data = resp.json()

                elif action == "get_contents":
                    path = self.get_config("path", "")
                    resp = await client.get(f"{base_api_url}/contents/{path}")
                    resp.raise_for_status()
                    result_data = resp.json()
                
                else:
                    return {"status": "error", "error": f"Unknown action: {action}"}

                return {
                    "status": "success",
                    "data": {
                        "result": result_data,
                        "id": result_data.get("id"),
                        "url": result_data.get("html_url") or result_data.get("url"),
                        "status": "completed"
                    }
                }

        except httpx.HTTPStatusError as e:
            return {"status": "error", "error": f"GitHub API Error ({e.response.status_code}): {e.response.text}"}
        except Exception as e:
            return {"status": "error", "error": f"GitHub Node execution failed: {str(e)}"}