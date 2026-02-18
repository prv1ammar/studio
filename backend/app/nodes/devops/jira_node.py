"""
Jira DevOps Node - Studio Standard
Batch 47: Developer Tools & Ops
"""
from typing import Any, Dict, Optional, List
import aiohttp
import base64
import json
from ..base import BaseNode
from ..registry import register_node

@register_node("jira_node")
class JiraNode(BaseNode):
    """
    Manage Jira issues and projects.
    Supports: Create Issue, Get Issue, List Projects, Add Comment.
    """
    node_type = "jira_node"
    version = "1.0.0"
    category = "devops"
    credentials_required = ["jira_auth"]


    properties = [
        {
            'displayName': 'Operation',
            'name': 'operation',
            'type': 'options',
            'default': 'create_issue',
            'options': [
                {'name': 'Create Issue', 'value': 'create_issue'},
                {'name': 'Get Issue', 'value': 'get_issue'},
                {'name': 'List Projects', 'value': 'list_projects'},
                {'name': 'Add Comment', 'value': 'add_comment'},
            ],
            'description': 'Jira action to perform',
        },
        {
            'displayName': 'Domain',
            'name': 'domain',
            'type': 'string',
            'default': '',
            'description': 'Atlassian domain (e.g., 'company.atlassian.net')',
            'required': True,
        },
        {
            'displayName': 'Issue Key',
            'name': 'issue_key',
            'type': 'string',
            'default': '',
            'description': 'Issue Key (e.g., 'PROJ-123')',
        },
        {
            'displayName': 'Payload',
            'name': 'payload',
            'type': 'string',
            'default': '',
            'description': 'Structured data for creation or comments',
        },
        {
            'displayName': 'Project Key',
            'name': 'project_key',
            'type': 'string',
            'default': '',
            'description': 'Project Key (e.g., 'PROJ')',
        },
    ]
    inputs = {
        "action": {
            "type": "dropdown",
            "default": "create_issue",
            "options": ["create_issue", "get_issue", "list_projects", "add_comment"],
            "description": "Jira action to perform"
        },
        "domain": {
            "type": "string",
            "required": True,
            "description": "Atlassian domain (e.g., 'company.atlassian.net')"
        },
        "project_key": {
            "type": "string",
            "optional": True,
            "description": "Project Key (e.g., 'PROJ')"
        },
        "issue_key": {
            "type": "string",
            "optional": True,
            "description": "Issue Key (e.g., 'PROJ-123')"
        },
        "payload": {
            "type": "json",
            "optional": True,
            "description": "Structured data for creation or comments"
        }
    }

    outputs = {
        "id": {"type": "string"},
        "key": {"type": "string"},
        "result": {"type": "any"},
        "url": {"type": "string"}
    }

    async def execute(self, input_data: Any, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        try:
            # 1. Resolve Auth
            creds = await self.get_credential("jira_auth")
            email = None
            token = None
            domain = self.get_config("domain")
            
            if creds:
                email = creds.get("email")
                token = creds.get("api_token") or creds.get("token")
            
            if not email or not token:
                email = self.get_config("email")
                token = self.get_config("api_token")

            if not all([email, token, domain]):
                return {"status": "error", "error": "Jira Email, API Token, and Domain are required."}

            # Auth Header
            auth_str = f"{email}:{token}"
            auth_b64 = base64.b64encode(auth_str.encode()).decode()
            headers = {
                "Authorization": f"Basic {auth_b64}",
                "Content-Type": "application/json",
                "Accept": "application/json"
            }

            action = self.get_config("action", "create_issue")
            base_url = f"https://{domain}/rest/api/3"

            async with aiohttp.ClientSession() as session:
                if action == "create_issue":
                    url = f"{base_url}/issue"
                    proj_key = self.get_config("project_key")
                    
                    data = self.get_config("payload", {})
                    if isinstance(input_data, dict):
                        data.update(input_data)
                    elif isinstance(input_data, str) and input_data:
                        data["summary"] = input_data
                    
                    # Ensure minimum fields
                    if "project" not in data and proj_key:
                        data["project"] = {"key": proj_key}
                    if "issuetype" not in data:
                        data["issuetype"] = {"name": "Task"}
                    if "summary" not in data:
                        return {"status": "error", "error": "Issue 'summary' is required."}

                    payload = {"fields": data}
                    async with session.post(url, json=payload, headers=headers) as resp:
                        result = await resp.json()
                        if resp.status >= 400:
                            return {"status": "error", "error": f"Jira API Error: {result.get('errorMessages') or result.get('errors')}"}
                        
                        issue_key = result.get("key")
                        return {
                            "status": "success",
                            "data": {
                                "id": result.get("id"),
                                "key": issue_key,
                                "url": f"https://{domain}/browse/{issue_key}",
                                "result": result
                            }
                        }

                elif action == "get_issue":
                    issue_key = self.get_config("issue_key") or (input_data if isinstance(input_data, str) else None)
                    if not issue_key:
                         return {"status": "error", "error": "Issue key is required."}
                    
                    url = f"{base_url}/issue/{issue_key}"
                    async with session.get(url, headers=headers) as resp:
                        result = await resp.json()
                        if resp.status >= 400:
                            return {"status": "error", "error": f"Jira API Error: {result.get('errorMessages')}"}
                        
                        return {
                            "status": "success",
                            "data": {
                                "id": result.get("id"),
                                "key": result.get("key"),
                                "result": result,
                                "status": result.get("fields", {}).get("status", {}).get("name")
                            }
                        }

                elif action == "add_comment":
                    issue_key = self.get_config("issue_key") or (input_data if isinstance(input_data, str) and "-" in input_data else None)
                    comment_text = self.get_config("payload", {}).get("body") or (input_data if isinstance(input_data, str) and "-" not in input_data else None)
                    
                    if not issue_key or not comment_text:
                         return {"status": "error", "error": "Issue key and comment body are required."}
                    
                    url = f"{base_url}/issue/{issue_key}/comment"
                    # Jira V3 uses Atlassian Document Format (ADF) for comments usually, 
                    # but simple string sometimes works or needs wrapper. 
                    # We'll use a simple ADF structure.
                    payload = {
                        "body": {
                            "type": "doc",
                            "version": 1,
                            "content": [
                                {
                                    "type": "paragraph",
                                    "content": [
                                        {
                                            "type": "text",
                                            "text": comment_text
                                        }
                                    ]
                                }
                            ]
                        }
                    }
                    async with session.post(url, json=payload, headers=headers) as resp:
                        result = await resp.json()
                        if resp.status >= 400:
                            return {"status": "error", "error": f"Jira API Error: {result.get('errorMessages')}"}
                        return {
                            "status": "success",
                            "data": {
                                "id": result.get("id"),
                                "result": result
                            }
                        }

                elif action == "list_projects":
                    url = f"{base_url}/project"
                    async with session.get(url, headers=headers) as resp:
                        result = await resp.json()
                        if resp.status >= 400:
                            return {"status": "error", "error": "Could not list projects."}
                        return {
                            "status": "success",
                            "data": {
                                "result": result,
                                "count": len(result)
                            }
                        }

                return {"status": "error", "error": f"Unsupported action: {action}"}

        except Exception as e:
            return {"status": "error", "error": f"Jira Node Failed: {str(e)}"}