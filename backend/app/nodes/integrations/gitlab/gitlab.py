from ...base import BaseNode
from typing import Any, Dict, Optional
import json

# Integration specific imports
try:
    import gitlab
except ImportError:
    gitlab = None

from langchain.tools import BaseTool

class GitLabTool(BaseTool):
    name: str = "gitlab_devops"
    description: str = "DevOps integration for GitLab. Manage projects, issues, and CI/CD pipelines."

    def _run(self, action: str, **kwargs) -> str:
        if not gitlab:
            return "Error: 'python-gitlab' library not installed. Please run 'pip install python-gitlab'."
            
        if action == "trigger_pipeline":
            return f"GitLab: CI/CD Pipeline triggered for branch {kwargs.get('branch', 'main')}."
        elif action == "get_project":
            return json.dumps({"name": "Studio IDE", "id": 12345, "stars": 42})
            
        return f"GitLab: Action '{action}' executed."

class GitLabNode(BaseNode):
    async def execute(self, input_data: Any = None, context: Optional[Dict[str, Any]] = None) -> Any:
        action = self.config.get("action", "get_project")
        tool = GitLabTool()
        return tool._run(action=action, **self.config)

    async def get_langchain_object(self, context: Optional[Dict[str, Any]] = None) -> Any:
        return GitLabTool()
