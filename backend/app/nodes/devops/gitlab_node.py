"""
GitLab DevOps Node - Studio Standard
Batch 45: DevOps & Infrastructure
"""
from typing import Any, Dict, Optional, List
import aiohttp
import json
import base64
from urllib.parse import quote_plus
from ...base import BaseNode
from ...registry import register_node

@register_node("gitlab_devops")
class GitLabDevOpsNode(BaseNode):
    """
    Manage GitLab resources: Issues, Merge Requests, Files, and Project Info.
    """
    node_type = "gitlab_devops"
    version = "1.0.0"
    category = "devops"
    credentials_required = ["gitlab_auth"]

    inputs = {
        "action": {
            "type": "dropdown",
            "default": "get_project_info",
            "options": [
                "get_project_info", 
                "create_issue", 
                "create_merge_request", 
                "list_repository_tree", 
                "get_file_content"
            ],
            "description": "Action to perform on GitLab"
        },
        "project_id": {
            "type": "string",
            "required": True,
            "description": "Project ID (numeric) or Path (e.g., 'group/project')"
        },
        "base_url": {
            "type": "string",
            "default": "https://gitlab.com",
            "description": "GitLab instance URL"
        },
        "path": {
            "type": "string",
            "optional": True,
            "description": "File or directory path"
        },
        "ref": {
            "type": "string",
            "default": "main",
            "description": "Branch, tag, or commit hash"
        },
        "data": {
            "type": "json",
            "optional": True,
            "description": "Structured data for creation (Issues/MRs)"
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
            creds = await self.get_credential("gitlab_auth")
            token = None
            if creds:
                token = creds.get("token") or creds.get("personal_access_token") or creds.get("private_token")
            
            if not token:
                token = self.get_config("personal_access_token")

            if not token:
                return {"status": "error", "error": "GitLab Private Token / PAT is required."}

            # 2. Setup API
            base_url = self.get_config("base_url", "https://gitlab.com").rstrip('/')
            project_id = self.get_config("project_id")
            # Encode project path if it contains slashes
            if "/" in project_id:
                project_id = quote_plus(project_id)
            
            action = self.get_config("action", "get_project_info")
            project_api_url = f"{base_url}/api/v4/projects/{project_id}"
            
            headers = {
                "PRIVATE-TOKEN": token,
                "Content-Type": "application/json"
            }

            async with aiohttp.ClientSession() as session:
                if action == "get_project_info":
                    async with session.get(project_api_url, headers=headers) as resp:
                        result = await resp.json()
                        if resp.status >= 400:
                            return {"status": "error", "error": f"GitLab Error: {result.get('message')}"}
                        return {
                            "status": "success",
                            "data": {
                                "result": result,
                                "url": result.get("web_url")
                            }
                        }

                elif action == "create_issue":
                    url = f"{project_api_url}/issues"
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
                            return {"status": "error", "error": f"GitLab Error: {result.get('message')}"}
                        return {
                            "status": "success",
                            "data": {
                                "result": result,
                                "url": result.get("web_url"),
                                "id": str(result.get("iid"))
                            }
                        }

                elif action == "create_merge_request":
                    url = f"{project_api_url}/merge_requests"
                    payload = self.get_config("data", {})
                    if isinstance(input_data, dict):
                        payload.update(input_data)
                    
                    if not all(k in payload for k in ["title", "source_branch", "target_branch"]):
                         return {"status": "error", "error": "MR requires 'title', 'source_branch', and 'target_branch'."}

                    async with session.post(url, json=payload, headers=headers) as resp:
                        result = await resp.json()
                        if resp.status >= 400:
                            return {"status": "error", "error": f"GitLab Error: {result.get('message')}"}
                        return {
                            "status": "success",
                            "data": {
                                "result": result,
                                "url": result.get("web_url"),
                                "id": str(result.get("iid"))
                            }
                        }

                elif action == "list_repository_tree":
                    path = self.get_config("path", "")
                    ref = self.get_config("ref", "main")
                    url = f"{project_api_url}/repository/tree"
                    params = {"path": path, "ref": ref}
                    async with session.get(url, headers=headers, params=params) as resp:
                        result = await resp.json()
                        if resp.status >= 400:
                            return {"status": "error", "error": f"GitLab Error: {result.get('message')}"}
                        return {
                            "status": "success",
                            "data": {
                                "result": result,
                                "count": len(result)
                            }
                        }

                elif action == "get_file_content":
                    path = self.get_config("path", "")
                    if not path:
                         return {"status": "error", "error": "File 'path' is required."}
                    
                    ref = self.get_config("ref", "main")
                    encoded_path = quote_plus(path)
                    url = f"{project_api_url}/repository/files/{encoded_path}"
                    params = {"ref": ref}
                    
                    async with session.get(url, headers=headers, params=params) as resp:
                        result = await resp.json()
                        if resp.status >= 400:
                            return {"status": "error", "error": f"GitLab Error: {result.get('message')}"}
                        
                        content_b64 = result.get("content")
                        content = base64.b64decode(content_b64).decode("utf-8")

                        return {
                            "status": "success",
                            "data": {
                                "result": content,
                                "metadata": {
                                    "blob_id": result.get("blob_id"),
                                    "size": result.get("size"),
                                    "last_commit_id": result.get("last_commit_id")
                                }
                            }
                        }

                return {"status": "error", "error": f"Unsupported action: {action}"}

        except Exception as e:
            return {"status": "error", "error": f"GitLab DevOps Node Failed: {str(e)}"}
