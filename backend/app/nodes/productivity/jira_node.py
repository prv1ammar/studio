"""
Jira Integration Node - Studio Standard
Part of Phase 6: Rewriting Existing Nodes to remove Composio
"""
import json
import base64
import httpx
from typing import Any, Dict, Optional, List
from ...base import BaseNode
from ...registry import register_node

@register_node("jira_node")
class JiraNode(BaseNode):
    """
    Interact with Jira Cloud directly via REST API.
    Supports: Create Issue, Get Issue, List Projects, Add Comment, Transition.
    Replaces Composio Jira implementation.
    """
    node_type = "jira_node"
    version = "1.0.0"
    category = "productivity"
    credentials_required = ["jira_auth"]

    inputs = {
        "action": {
            "type": "dropdown",
            "default": "get_issue",
            "options": [
                "get_issue",
                "create_issue",
                "list_projects",
                "add_comment",
                "transition_issue"
            ],
            "description": "Action to perform"
        },
        "domain": {
            "type": "string",
            "required": True,
            "description": "Jira domain (e.g., your-domain.atlassian.net)"
        },
        "issue_key": {
            "type": "string",
            "optional": True,
            "description": "Issue key (e.g., PROJ-123)"
        },
        "project_key": {
            "type": "string",
            "optional": True,
            "description": "Project key for creating issues"
        },
        "summary": {
            "type": "string",
            "optional": True,
            "description": "Issue summary"
        },
        "description": {
            "type": "string",
            "optional": True,
            "description": "Issue description"
        },
        "issue_type": {
            "type": "string",
            "default": "Task",
            "description": "Issue type (Task, Bug, Story, etc.)"
        },
        "comment_body": {
            "type": "string",
            "optional": True,
            "description": "Comment text"
        },
        "transition_id": {
            "type": "string",
            "optional": True,
            "description": "Transition ID for status changes"
        }
    }

    outputs = {
        "result": {"type": "json"},
        "key": {"type": "string"},
        "id": {"type": "string"},
        "status": {"type": "string"}
    }

    async def execute(self, input_data: Any, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        try:
            # 1. Get Credentials
            creds = await self.get_credential("jira_auth")
            if not creds:
                 return {"status": "error", "error": "Jira credentials (jira_auth) are required."}
            
            email = creds.get("email")
            api_token = creds.get("api_token") or creds.get("token")
            
            if not email or not api_token:
                 return {"status": "error", "error": "Jira credentials must contain 'email' and 'api_token'."}

            # 2. Setup Auth
            auth_str = f"{email}:{api_token}"
            encoded_auth = base64.b64encode(auth_str.encode()).decode()
            
            headers = {
                "Authorization": f"Basic {encoded_auth}",
                "Accept": "application/json",
                "Content-Type": "application/json"
            }
            
            domain = self.get_config("domain")
            if not domain:
                 return {"status": "error", "error": "Jira domain is required."}
            
            if not domain.startswith("http"):
                domain = f"https://{domain}"
            
            action = self.get_config("action", "get_issue")
            
            async with httpx.AsyncClient(headers=headers, timeout=30.0) as client:
                
                result_data = {}
                
                if action == "get_issue":
                    issue_key = self.get_config("issue_key") or (input_data if isinstance(input_data, str) else None)
                    if not issue_key:
                         return {"status": "error", "error": "Issue key is required for get_issue."}
                    
                    resp = await client.get(f"{domain}/rest/api/3/issue/{issue_key}")
                    resp.raise_for_status()
                    result_data = resp.json()

                elif action == "create_issue":
                    project_key = self.get_config("project_key")
                    summary = self.get_config("summary") or (input_data if isinstance(input_data, str) else "New Issue from Studio")
                    description = self.get_config("description") or ""
                    issue_type = self.get_config("issue_type", "Task")
                    
                    if not project_key:
                        return {"status": "error", "error": "Project key is required for creating an issue."}
                        
                    payload = {
                        "fields": {
                            "project": {"key": project_key},
                            "summary": summary,
                            "description": {
                                "type": "doc",
                                "version": 1,
                                "content": [
                                    {
                                        "type": "paragraph",
                                        "content": [{"type": "text", "text": description}]
                                    }
                                ]
                            },
                            "issuetype": {"name": issue_type}
                        }
                    }
                    resp = await client.post(f"{domain}/rest/api/3/issue", json=payload)
                    resp.raise_for_status()
                    result_data = resp.json()

                elif action == "list_projects":
                    resp = await client.get(f"{domain}/rest/api/3/project")
                    resp.raise_for_status()
                    projects = resp.json()
                    result_data = {"projects": projects, "count": len(projects)}

                elif action == "add_comment":
                    issue_key = self.get_config("issue_key")
                    comment = self.get_config("comment_body") or (input_data if isinstance(input_data, str) else "")
                    
                    if not issue_key or not comment:
                        return {"status": "error", "error": "Issue key and comment body are required."}
                        
                    payload = {
                        "body": {
                            "type": "doc",
                            "version": 1,
                            "content": [
                                {
                                    "type": "paragraph",
                                    "content": [{"type": "text", "text": comment}]
                                }
                            ]
                        }
                    }
                    resp = await client.post(f"{domain}/rest/api/3/issue/{issue_key}/comment", json=payload)
                    resp.raise_for_status()
                    result_data = resp.json()

                elif action == "transition_issue":
                    issue_key = self.get_config("issue_key")
                    transition_id = self.get_config("transition_id")
                    
                    if not issue_key or not transition_id:
                        return {"status": "error", "error": "Issue key and transition ID are required."}
                        
                    payload = {"transition": {"id": transition_id}}
                    resp = await client.post(f"{domain}/rest/api/3/issue/{issue_key}/transitions", json=payload)
                    resp.raise_for_status()
                    result_data = {"status": "success", "message": f"Issue {issue_key} transitioned."}
                
                else:
                    return {"status": "error", "error": f"Unknown action: {action}"}

                return {
                    "status": "success",
                    "data": {
                        "result": result_data,
                        "key": result_data.get("key"),
                        "id": result_data.get("id"),
                        "status": "completed"
                    }
                }

        except httpx.HTTPStatusError as e:
            return {"status": "error", "error": f"Jira API Error ({e.response.status_code}): {e.response.text}"}
        except Exception as e:
            return {"status": "error", "error": f"Jira Node execution failed: {str(e)}"}
