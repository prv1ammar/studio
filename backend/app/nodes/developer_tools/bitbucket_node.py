"""
Bitbucket Node - Studio Standard (Universal Method)
Batch 110: Developer Tools & Databases
"""
from typing import Any, Dict, Optional
import aiohttp
from ..base import BaseNode
from ..registry import register_node

@register_node("bitbucket_node")
class BitbucketNode(BaseNode):
    """
    Bitbucket integration for version control.
    """
    node_type = "bitbucket_node"
    version = "1.0.0"
    category = "developer_tools"
    credentials_required = ["bitbucket_auth"]


    properties = [
        {
            'displayName': 'Operation',
            'name': 'operation',
            'type': 'options',
            'default': 'create_issue',
            'options': [
                {'name': 'Create Issue', 'value': 'create_issue'},
                {'name': 'List Repos', 'value': 'list_repos'},
                {'name': 'Get Commit', 'value': 'get_commit'},
            ],
            'description': 'Bitbucket action',
        },
        {
            'displayName': 'Repo Slug',
            'name': 'repo_slug',
            'type': 'string',
            'default': '',
        },
        {
            'displayName': 'Title',
            'name': 'title',
            'type': 'string',
            'default': '',
        },
        {
            'displayName': 'Workspace',
            'name': 'workspace',
            'type': 'string',
            'default': '',
        },
    ]
    inputs = {
        "action": {
            "type": "dropdown",
            "default": "create_issue",
            "options": ["create_issue", "list_repos", "get_commit"],
            "description": "Bitbucket action"
        },
        "workspace": {
            "type": "string",
            "optional": True
        },
        "repo_slug": {
            "type": "string",
            "optional": True
        },
        "title": {
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
            creds = await self.get_credential("bitbucket_auth")
            username = creds.get("username")
            app_password = creds.get("app_password")
            
            if not username or not app_password:
                return {"status": "error", "error": "Bitbucket username and App Password required"}

            base_url = "https://api.bitbucket.org/2.0"
            auth = aiohttp.BasicAuth(username, app_password)
            headers = {"Content-Type": "application/json"}
            
            action = self.get_config("action", "create_issue")

            async with aiohttp.ClientSession() as session:
                if action == "create_issue":
                    workspace = self.get_config("workspace")
                    repo_slug = self.get_config("repo_slug")
                    title = self.get_config("title")
                    
                    if not workspace or not repo_slug or not title:
                        return {"status": "error", "error": "workspace, repo_slug, and title required"}
                        
                    payload = {
                        "title": title,
                        "content": {"raw": self.get_config("content", "")}
                    }
                    
                    url = f"{base_url}/repositories/{workspace}/{repo_slug}/issues"
                    async with session.post(url, headers=headers, auth=auth, json=payload) as resp:
                         if resp.status != 201:
                            error_text = await resp.text()
                            return {"status": "error", "error": f"Bitbucket API Error {resp.status}: {error_text}"}
                         res_data = await resp.json()
                         return {"status": "success", "data": {"result": res_data}}
                
                elif action == "list_repos":
                     workspace = self.get_config("workspace")
                     url = f"{base_url}/repositories/{workspace}" if workspace else f"{base_url}/repositories"
                     async with session.get(url, headers=headers, auth=auth) as resp:
                         res_data = await resp.json()
                         return {"status": "success", "data": {"result": res_data.get("values", [])}}
                
                elif action == "get_commit":
                    workspace = self.get_config("workspace")
                    repo_slug = self.get_config("repo_slug")
                    commit = self.get_config("commit_hash")
                    if not commit: return {"status": "error", "error": "commit_hash required"}
                    
                    url = f"{base_url}/repositories/{workspace}/{repo_slug}/commit/{commit}"
                    async with session.get(url, headers=headers, auth=auth) as resp:
                         res_data = await resp.json()
                         return {"status": "success", "data": {"result": res_data}}

            return {"status": "error", "error": f"Unsupported action: {action}"}

        except Exception as e:
            return {"status": "error", "error": f"Bitbucket Node Failed: {str(e)}"}