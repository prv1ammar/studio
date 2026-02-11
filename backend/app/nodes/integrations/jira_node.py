import aiohttp
import json
import base64
from typing import Any, Dict, Optional
from pydantic import Field
from app.nodes.base import BaseNode, NodeConfig
from app.nodes.registry import register_node

class JiraConfig(NodeConfig):
    domain: Optional[str] = Field(None, description="Jira Instance Domain (e.g. yourcompany.atlassian.net)")
    email: Optional[str] = Field(None, description="Jira Account Email")
    api_token: Optional[str] = Field(None, description="Jira API Token")
    project_key: Optional[str] = Field(None, description="Jira Project Key (e.g. PROJ)")
    credentials_id: Optional[str] = Field(None, description="Jira Credentials ID")
    action: str = Field("create_issue", description="Action (create_issue, get_issue)")

@register_node("jira_node")
class JiraNode(BaseNode):
    node_id = "jira_node"
    config_model = JiraConfig

    async def execute(self, input_data: Any, context: Optional[Dict[str, Any]] = None) -> Any:
        # 1. Auth Retrieval
        creds = await self.get_credential("credentials_id")
        domain = self.get_config("domain")
        email = creds.get("email") if creds else self.get_config("email")
        token = creds.get("token") if creds else self.get_config("api_token")
        project_key = self.get_config("project_key")

        if not domain or not email or not token:
            return {"error": "Jira Domain, Email, and API Token are required."}

        action = self.get_config("action")
        
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
                    
                    # input_data can be title or full fields
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
                            return {"error": f"Jira API Error: {result.get('errorMessages') or result.get('errors')}"}
                        return {"status": "success", "issue_key": result.get("key"), "id": result.get("id")}

                elif action == "get_issue":
                    issue_key = input_data if isinstance(input_data, str) else None
                    if not issue_key:
                        return {"error": "Issue key is required to fetch issue info."}
                        
                    url = f"https://{domain}/rest/api/3/issue/{issue_key}"
                    async with session.get(url, headers=headers) as resp:
                        result = await resp.json()
                        if resp.status >= 400:
                            return {"error": f"Jira API Error: {result.get('errorMessages')}"}
                        return {
                            "id": result.get("id"),
                            "key": result.get("key"),
                            "status": result.get("fields", {}).get("status", {}).get("name"),
                            "summary": result.get("fields", {}).get("summary"),
                            "description": result.get("fields", {}).get("description")
                        }

                return {"error": f"Unsupported Jira action: {action}"}

            except Exception as e:
                return {"error": f"Jira Node Failed: {str(e)}"}
