import aiohttp
import json
import base64
from typing import Any, Dict, Optional
from ..base import BaseNode
from ..registry import register_node

@register_node("jira_action")
class JiraNode(BaseNode):
    """Integrates with Jira for issue management."""
    node_type = "jira_action"
    version = "1.0.0"
    category = "integrations"
    credentials_required = ["jira_auth"]

    inputs = {
        "action": {"type": "string", "enum": ["create_issue", "get_issue"], "default": "create_issue"},
        "domain": {"type": "string", "description": "e.g. company.atlassian.net"},
        "project_key": {"type": "string", "description": "e.g. PROJ"},
        "data": {"type": "any", "description": "Issue summary or full fields dict"}
    }
    outputs = {
        "result": {"type": "object"},
        "status": {"type": "string"}
    }

    async def execute(self, input_data: Any, context: Optional[Dict[str, Any]] = None) -> Any:
        # 1. Auth Retrieval
        creds = await self.get_credential("jira_auth")
        domain = self.get_config("domain")
        email = creds.get("email") if creds else self.get_config("email")
        token = creds.get("token") or creds.get("api_token") if creds else self.get_config("api_token")
        project_key = self.get_config("project_key")

        if not domain or not email or not token:
            return {"status": "error", "error": "Jira Domain, Email, and API Token are required.", "data": None}

        action = self.get_config("action", "create_issue")
        
        # Basic Auth for Jira Cloud
        auth_string = f"{email}:{token}"
        auth_encoded = base64.b64encode(auth_string.encode()).decode()
        
        headers = {
            "Authorization": f"Basic {auth_encoded}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }

        async with aiohttp.ClientSession() as session:
            try:
                if action == "create_issue":
                    url = f"https://{domain}/rest/api/3/issue"
                    
                    if isinstance(input_data, dict):
                        fields = input_data
                        if "project" not in fields:
                            fields["project"] = {"key": project_key}
                    else:
                        fields = {
                            "project": {"key": project_key},
                            "summary": str(input_data),
                            "issuetype": {"name": "Task"}
                        }
                    
                    payload = {"fields": fields}
                    
                    async with session.post(url, json=payload, headers=headers) as resp:
                        result = await resp.json()
                        if resp.status >= 400:
                            return {"status": "error", "error": f"Jira API Error: {result.get('errorMessages') or result.get('errors')}", "data": result}
                        return {
                            "status": "success", 
                            "data": {
                                "issue_key": result.get("key"), 
                                "id": result.get("id"),
                                "url": f"https://{domain}/browse/{result.get('key')}"
                            }
                        }

                elif action == "get_issue":
                    issue_key = input_data if isinstance(input_data, str) else None
                    if not issue_key:
                        return {"status": "error", "error": "Issue key is required to fetch issue info.", "data": None}
                        
                    url = f"https://{domain}/rest/api/3/issue/{issue_key}"
                    async with session.get(url, headers=headers) as resp:
                        result = await resp.json()
                        if resp.status >= 400:
                            return {"status": "error", "error": f"Jira API Error: {result.get('errorMessages')}", "data": result}
                        return {
                            "status": "success",
                            "data": {
                                "id": result.get("id"),
                                "key": result.get("key"),
                                "status": result.get("fields", {}).get("status", {}).get("name"),
                                "summary": result.get("fields", {}).get("summary"),
                                "description": result.get("fields", {}).get("description")
                            }
                        }

                return {"status": "error", "error": f"Unsupported Jira action: {action}", "data": None}

            except Exception as e:
                return {"status": "error", "error": f"Jira Node Failed: {str(e)}", "data": None}
