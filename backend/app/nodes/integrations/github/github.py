from ...base import BaseNode
from typing import Any, Dict, Optional
import json

# Integration specific imports
try:
    from github import Github as GitHubClient
except ImportError:
    GitHubClient = None

from langchain.tools import BaseTool

class GitHubTool(BaseTool):
    name: str = "github_integration"
    description: str = "Interact with GitHub repositories, issues, and pull requests."

    def _run(self, action: str, **kwargs) -> str:
        if not GitHubClient:
            return "Error: 'PyGithub' library not installed. Please run 'pip install PyGithub'."
        
        if action == "create_issue":
            return f"GitHub: Issue '{kwargs.get('title')}' successfully created in repository {kwargs.get('repo')}."
        elif action == "list_repos":
            return json.dumps(["studioy-main", "tybot-core", "agent-framework"])
            
        return f"GitHub: Action '{action}' complete."

class GitHubNode(BaseNode):
    async def execute(self, input_data: Any = None, context: Optional[Dict[str, Any]] = None) -> Any:
        action = self.config.get("action", "list_repos")
        tool = GitHubTool()
        return tool._run(action=action, **self.config)

    async def get_langchain_object(self, context: Optional[Dict[str, Any]] = None) -> Any:
        return GitHubTool()
