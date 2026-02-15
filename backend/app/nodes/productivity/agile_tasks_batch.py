"""
Agile & Task Management Nodes - Studio Standard (Universal Method)
Batch 105: Productivity Suite
"""
from typing import Any, Dict, Optional, List
import aiohttp
from ...base import BaseNode
from ...registry import register_node

# ============================================
# LINEAR NODE
# ============================================
@register_node("linear_node")
class LinearNode(BaseNode):
    """
    Linear issue tracking integration for software teams.
    """
    node_type = "linear_node"
    version = "1.0.0"
    category = "productivity"
    credentials_required = ["linear_auth"]

    inputs = {
        "action": {
            "type": "dropdown",
            "default": "create_issue",
            "options": ["create_issue", "list_issues", "update_issue", "get_team", "list_teams"],
            "description": "Linear action"
        },
        "team_id": {
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
        },
        "state_id": {
            "type": "string",
            "optional": True
        },
        "assignee_id": {
            "type": "string",
            "optional": True
        },
        "issue_id": {
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
            creds = await self.get_credential("linear_auth")
            api_key = creds.get("api_key")
            
            if not api_key:
                return {"status": "error", "error": "Linear API key required"}

            url = "https://api.linear.app/graphql"
            headers = {
                "Authorization": api_key,
                "Content-Type": "application/json"
            }
            
            action = self.get_config("action", "create_issue")

            async with aiohttp.ClientSession() as session:
                if action == "create_issue":
                    team_id = self.get_config("team_id")
                    title = self.get_config("title")
                    description = self.get_config("description", "")
                    
                    if not team_id or not title:
                        return {"status": "error", "error": "team_id and title required"}
                    
                    # Construct GraphQL mutation
                    mutation = """
                    mutation IssueCreate($input: IssueCreateInput!) {
                        issueCreate(input: $input) {
                            success
                            issue {
                                id
                                title
                                number
                                url
                            }
                        }
                    }
                    """
                    
                    variables = {
                        "input": {
                            "teamId": team_id,
                            "title": title,
                            "description": description
                        }
                    }
                    
                    if self.get_config("state_id"):
                        variables["input"]["stateId"] = self.get_config("state_id")
                    if self.get_config("assignee_id"):
                        variables["input"]["assigneeId"] = self.get_config("assignee_id")
                    
                    payload = {"query": mutation, "variables": variables}
                    
                    async with session.post(url, headers=headers, json=payload) as resp:
                        if resp.status != 200:
                            error_text = await resp.text()
                            return {"status": "error", "error": f"Linear API Error {resp.status}: {error_text}"}
                        res_data = await resp.json()
                        
                        if "errors" in res_data:
                            return {"status": "error", "error": f"Linear GraphQL Error: {res_data['errors']}"}
                            
                        return {"status": "success", "data": {"result": res_data.get("data", {}).get("issueCreate", {})}}

                elif action == "list_issues":
                    # Simple query to list recent issues
                    query = """
                    query Issues($first: Int) {
                        issues(first: $first) {
                            nodes {
                                id
                                title
                                number
                                state {
                                    name
                                }
                            }
                        }
                    }
                    """
                    variables = {"first": 50}
                    
                    async with session.post(url, headers=headers, json={"query": query, "variables": variables}) as resp:
                        if resp.status != 200:
                            error_text = await resp.text()
                            return {"status": "error", "error": f"Linear API Error {resp.status}: {error_text}"}
                        res_data = await resp.json()
                        return {"status": "success", "data": {"result": res_data.get("data", {}).get("issues", {}).get("nodes", [])}}

                elif action == "list_teams":
                    query = """
                    query {
                        teams {
                            nodes {
                                id
                                name
                                key
                            }
                        }
                    }
                    """
                    async with session.post(url, headers=headers, json={"query": query}) as resp:
                        if resp.status != 200:
                            error_text = await resp.text()
                            return {"status": "error", "error": f"Linear API Error {resp.status}: {error_text}"}
                        res_data = await resp.json()
                        return {"status": "success", "data": {"result": res_data.get("data", {}).get("teams", {}).get("nodes", [])}}

            return {"status": "error", "error": f"Unsupported action: {action}"}

        except Exception as e:
            return {"status": "error", "error": f"Linear Node Failed: {str(e)}"}


# ============================================
# BASECAMP NODE
# ============================================
@register_node("basecamp_node")
class BasecampNode(BaseNode):
    """
    Basecamp 3 integration for project management.
    """
    node_type = "basecamp_node"
    version = "1.0.0"
    category = "productivity"
    credentials_required = ["basecamp_auth"]

    inputs = {
        "action": {
            "type": "dropdown",
            "default": "create_todo",
            "options": ["create_todo", "list_todos", "create_message", "list_projects"],
            "description": "Basecamp action"
        },
        "account_id": {
            "type": "string",
            "optional": True
        },
        "project_id": {
            "type": "string",
            "optional": True
        },
        "todolist_id": {
            "type": "string",
            "optional": True
        },
        "content": {
            "type": "string",
            "optional": True
        },
        "message_board_id": {
            "type": "string",
            "optional": True
        },
        "subject": {
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
            creds = await self.get_credential("basecamp_auth")
            access_token = creds.get("access_token")
            account_id = creds.get("account_id") or self.get_config("account_id")
            
            if not access_token or not account_id:
                return {"status": "error", "error": "Basecamp access token and account ID required"}

            base_url = f"https://3.basecampapi.com/{account_id}"
            headers = {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json",
                "User-Agent": "Studio Automation (support@example.com)"
            }
            
            action = self.get_config("action", "create_todo")

            async with aiohttp.ClientSession() as session:
                if action == "create_todo":
                    project_id = self.get_config("project_id")
                    todolist_id = self.get_config("todolist_id")
                    content = self.get_config("content")
                    
                    if not all([project_id, todolist_id, content]):
                        return {"status": "error", "error": "project_id, todolist_id, and content required"}
                    
                    url = f"{base_url}/buckets/{project_id}/todolists/{todolist_id}/todos.json"
                    payload = {"content": content}
                    
                    async with session.post(url, headers=headers, json=payload) as resp:
                        if resp.status != 201:
                            error_text = await resp.text()
                            return {"status": "error", "error": f"Basecamp API Error {resp.status}: {error_text}"}
                        res_data = await resp.json()
                        return {"status": "success", "data": {"result": res_data}}

                elif action == "list_projects":
                    url = f"{base_url}/projects.json"
                    async with session.get(url, headers=headers) as resp:
                        if resp.status != 200:
                            error_text = await resp.text()
                            return {"status": "error", "error": f"Basecamp API Error {resp.status}: {error_text}"}
                        res_data = await resp.json()
                        return {"status": "success", "data": {"result": res_data}}

            return {"status": "error", "error": f"Unsupported action: {action}"}

        except Exception as e:
            return {"status": "error", "error": f"Basecamp Node Failed: {str(e)}"}


# ============================================
# TODOIST NODE
# ============================================
@register_node("todoist_node")
class TodoistNode(BaseNode):
    """
    Todoist task management integration.
    """
    node_type = "todoist_node"
    version = "1.0.0"
    category = "productivity"
    credentials_required = ["todoist_auth"]

    inputs = {
        "action": {
            "type": "dropdown",
            "default": "create_task",
            "options": ["create_task", "list_tasks", "update_task", "close_task", "list_projects"],
            "description": "Todoist action"
        },
        "content": {
            "type": "string",
            "optional": True,
            "description": "Task content"
        },
        "project_id": {
            "type": "string",
            "optional": True
        },
        "due_string": {
            "type": "string",
            "optional": True,
            "description": "Natural language due date (e.g. 'tomorrow at 12')"
        },
        "task_id": {
            "type": "string",
            "optional": True
        },
        "priority": {
            "type": "number",
            "optional": True,
            "description": "1 (normal) to 4 (urgent)"
        }
    }

    outputs = {
        "result": {"type": "any"},
        "status": {"type": "string"}
    }

    async def execute(self, input_data: Any, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        try:
            creds = await self.get_credential("todoist_auth")
            api_token = creds.get("api_token")
            
            if not api_token:
                return {"status": "error", "error": "Todoist API token required"}

            base_url = "https://api.todoist.com/rest/v2"
            headers = {
                "Authorization": f"Bearer {api_token}",
                "Content-Type": "application/json"
            }
            
            action = self.get_config("action", "create_task")

            async with aiohttp.ClientSession() as session:
                if action == "create_task":
                    content = self.get_config("content")
                    if not content:
                        return {"status": "error", "error": "content required"}
                    
                    payload = {"content": content}
                    
                    if self.get_config("project_id"):
                        payload["project_id"] = self.get_config("project_id")
                    if self.get_config("due_string"):
                        payload["due_string"] = self.get_config("due_string")
                    if self.get_config("priority"):
                        payload["priority"] = int(self.get_config("priority"))
                    
                    url = f"{base_url}/tasks"
                    async with session.post(url, headers=headers, json=payload) as resp:
                        if resp.status != 200:
                            error_text = await resp.text()
                            return {"status": "error", "error": f"Todoist API Error {resp.status}: {error_text}"}
                        res_data = await resp.json()
                        return {"status": "success", "data": {"result": res_data}}

                elif action == "list_tasks":
                    url = f"{base_url}/tasks"
                    params = {}
                    if self.get_config("project_id"):
                        params["project_id"] = self.get_config("project_id")
                        
                    async with session.get(url, headers=headers, params=params) as resp:
                        if resp.status != 200:
                            error_text = await resp.text()
                            return {"status": "error", "error": f"Todoist API Error {resp.status}: {error_text}"}
                        res_data = await resp.json()
                        return {"status": "success", "data": {"result": res_data}}

                elif action == "close_task":
                    task_id = self.get_config("task_id") or str(input_data)
                    if not task_id:
                        return {"status": "error", "error": "task_id required"}
                    
                    url = f"{base_url}/tasks/{task_id}/close"
                    async with session.post(url, headers=headers) as resp:
                        if resp.status != 204:
                            error_text = await resp.text()
                            return {"status": "error", "error": f"Todoist API Error {resp.status}: {error_text}"}
                        return {"status": "success", "data": {"result": {"message": "Task closed"}}}

            return {"status": "error", "error": f"Unsupported action: {action}"}

        except Exception as e:
            return {"status": "error", "error": f"Todoist Node Failed: {str(e)}"}
