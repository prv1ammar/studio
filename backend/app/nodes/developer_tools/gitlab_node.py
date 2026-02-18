"""
GitLab Node - Studio Standard (Universal Method)
Batch 110: Developer Tools & Databases
"""
from typing import Any, Dict, Optional
import aiohttp
from ..base import BaseNode
from ..registry import register_node

@register_node("gitlab_node")
class GitLabNode(BaseNode):
    """
    GitLab integration for DevOps lifecycle.
    """
    node_type = "gitlab_node"
    version = "1.0.0"
    category = "developer_tools"
    credentials_required = ["gitlab_auth"]


    properties = [
        {
            'displayName': 'Operation',
            'name': 'operation',
            'type': 'options',
            'default': 'create_issue',
            'options': [
                {'name': 'Create Issue', 'value': 'create_issue'},
                {'name': 'List Projects', 'value': 'list_projects'},
                {'name': 'Create Mr', 'value': 'create_mr'},
                {'name': 'Get File', 'value': 'get_file'},
            ],
            'description': 'GitLab action',
        },
        {
            'displayName': 'Description',
            'name': 'description',
            'type': 'string',
            'default': '',
        },
        {
            'displayName': 'Project Id',
            'name': 'project_id',
            'type': 'string',
            'default': '',
        },
        {
            'displayName': 'Title',
            'name': 'title',
            'type': 'string',
            'default': '',
        },
    ]
    inputs = {
        "action": {
            "type": "dropdown",
            "default": "create_issue",
            "options": ["create_issue", "list_projects", "create_mr", "get_file"],
            "description": "GitLab action"
        },
        "project_id": {
            "type": "string",
            "optional": True
        },
        "title": {
            "type": "string",
            "optional": True
        },
        "description": {
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
            creds = await self.get_credential("gitlab_auth")
            access_token = creds.get("access_token")
            base_url = creds.get("base_url", "https://gitlab.com")
            
            if not access_token:
                return {"status": "error", "error": "GitLab access token required"}

            api_url = f"{base_url}/api/v4"
            headers = {"Authorization": f"Bearer {access_token}"}
            
            action = self.get_config("action", "create_issue")

            async with aiohttp.ClientSession() as session:
                if action == "create_issue":
                    project_id = self.get_config("project_id")
                    title = self.get_config("title")
                    description = self.get_config("description", "")
                    
                    if not project_id or not title:
                        return {"status": "error", "error": "project_id and title required"}
                        
                    # Encoded project ID might be needed if using 'group/project', but ID (int) is safer
                    payload = {"title": title, "description": description}
                    
                    url = f"{api_url}/projects/{project_id}/issues"
                    async with session.post(url, headers=headers, json=payload) as resp:
                         if resp.status != 201:
                            error_text = await resp.text()
                            return {"status": "error", "error": f"GitLab API Error {resp.status}: {error_text}"}
                         res_data = await resp.json()
                         return {"status": "success", "data": {"result": res_data}}
                
                elif action == "list_projects":
                     url = f"{api_url}/projects"
                     async with session.get(url, headers=headers) as resp:
                         res_data = await resp.json()
                         return {"status": "success", "data": {"result": res_data}}

                elif action == "get_file":
                    project_id = self.get_config("project_id")
                    file_path = self.get_config("file_path") # Need input
                    ref = self.get_config("ref", "main")
                    
                    if not file_path: return {"status": "error", "error": "file_path required"}
                    
                    # URL encode file path
                    import urllib.parse
                    encoded_path = urllib.parse.quote(file_path, safe='')
                    
                    url = f"{api_url}/projects/{project_id}/repository/files/{encoded_path}/raw?ref={ref}"
                    async with session.get(url, headers=headers) as resp:
                         if resp.status != 200:
                             return {"status": "error", "error": f"File not found or access denied: {resp.status}"}
                         content = await resp.text()
                         return {"status": "success", "data": {"result": content}}

            return {"status": "error", "error": f"Unsupported action: {action}"}

        except Exception as e:
            return {"status": "error", "error": f"GitLab Node Failed: {str(e)}"}