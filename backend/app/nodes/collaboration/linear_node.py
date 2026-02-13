"""
Linear Node - Studio Standard
Batch 69: Project Collaboration
"""
from typing import Any, Dict, Optional, List
import aiohttp
from ...base import BaseNode
from ...registry import register_node

@register_node("linear_node")
class LinearNode(BaseNode):
    """
    Automate issue tracking and engineering workflows via Linear GraphQL API.
    """
    node_type = "linear_node"
    version = "1.0.0"
    category = "collaboration"
    credentials_required = ["linear_auth"]

    inputs = {
        "action": {
            "type": "dropdown",
            "default": "list_issues",
            "options": ["list_issues", "create_issue", "list_teams", "get_viewer"],
            "description": "Linear action"
        },
        "team_id": {
            "type": "string",
            "optional": True,
            "description": "ID of the team"
        },
        "title": {
            "type": "string",
            "optional": True,
            "description": "Issue title"
        },
        "description": {
            "type": "string",
            "optional": True
        }
    }

    outputs = {
        "result": {"type": "any"},
        "status": {"type": "string"},
        "count": {"type": "number"}
    }

    async def execute(self, input_data: Any, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        try:
            creds = await self.get_credential("linear_auth")
            api_key = creds.get("api_key") if creds else self.get_config("api_key")
            
            if not api_key:
                return {"status": "error", "error": "Linear API Key is required."}

            headers = {
                "Authorization": api_key,
                "Content-Type": "application/json"
            }
            
            base_url = "https://api.linear.app/graphql"
            action = self.get_config("action", "list_issues")

            async with aiohttp.ClientSession() as session:
                if action == "get_viewer":
                    query = "{ viewer { id name email } }"
                    async with session.post(base_url, headers=headers, json={"query": query}) as resp:
                        res_data = await resp.json()
                        return {"status": "success", "data": {"result": res_data.get("data", {}).get("viewer")}}

                elif action == "list_teams":
                    query = "{ teams { nodes { id name key } } }"
                    async with session.post(base_url, headers=headers, json={"query": query}) as resp:
                        res_data = await resp.json()
                        teams = res_data.get("data", {}).get("teams", {}).get("nodes", [])
                        return {"status": "success", "data": {"result": teams, "count": len(teams)}}

                elif action == "list_issues":
                    team_id = self.get_config("team_id")
                    if team_id:
                        query = f"{{ team(id: \"{team_id}\") {{ issues {{ nodes {{ id title identifier status {{ name }} }} }} }} }}"
                        key = "team"
                    else:
                        query = "{ issues { nodes { id title identifier status { name } } } }"
                        key = "issues"
                        
                    async with session.post(base_url, headers=headers, json={"query": query}) as resp:
                        res_data = await resp.json()
                        if key == "team":
                            issues = res_data.get("data", {}).get("team", {}).get("issues", {}).get("nodes", [])
                        else:
                            issues = res_data.get("data", {}).get("issues", {}).get("nodes", [])
                        return {"status": "success", "data": {"result": issues, "count": len(issues)}}

                elif action == "create_issue":
                    team_id = self.get_config("team_id")
                    if not team_id:
                        return {"status": "error", "error": "team_id is required to create an issue."}
                    
                    title = self.get_config("title") or str(input_data)
                    description = self.get_config("description", "")
                    
                    query = """
                    mutation($teamId: String!, $title: String!, $description: String) {
                      issueCreate(input: { teamId: $teamId, title: $title, description: $description }) {
                        success
                        issue { id title identifier }
                      }
                    }
                    """
                    variables = {"teamId": team_id, "title": title, "description": description}
                    async with session.post(base_url, headers=headers, json={"query": query, "variables": variables}) as resp:
                        res_data = await resp.json()
                        create_data = res_data.get("data", {}).get("issueCreate", {})
                        return {"status": "success", "data": {"result": create_data.get("issue"), "success": create_data.get("success")}}

                return {"status": "error", "error": f"Unsupported action: {action}"}

        except Exception as e:
            return {"status": "error", "error": f"Linear Node Failed: {str(e)}"}
