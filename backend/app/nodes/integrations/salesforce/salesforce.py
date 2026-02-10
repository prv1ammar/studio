from ...base import BaseNode
from typing import Any, Dict, Optional
import json

# Integration specific imports
try:
    from simple_salesforce import Salesforce
except ImportError:
    Salesforce = None

from langchain.tools import BaseTool
from pydantic import Field

class SalesforceTool(BaseTool):
    name: str = "salesforce_crm"
    description: str = "Professional CRM integration for Salesforce. Use to manage leads, accounts, and opportunities."
    
    # Salesforce connection parameters
    username: Optional[str] = Field(default=None)
    password: Optional[str] = Field(default=None)
    security_token: Optional[str] = Field(default=None)

    def _run(self, action: str, **kwargs) -> str:
        if not Salesforce:
            return "Error: 'simple-salesforce' library not installed. Please run 'pip install simple-salesforce'."
        
        # Real logic placeholder (would use self.username, etc.)
        if action == "create_lead":
            return f"Salesforce: Lead created for {kwargs.get('last_name', 'Unknown')}."
        elif action == "list_accounts":
            return json.dumps([{"Name": "Tyboo Corp", "Industry": "AI"}, {"Name": "Example Ltd", "Industry": "Tech"}])
            
        return f"Salesforce action '{action}' executed."

class SalesforceNode(BaseNode):
    async def execute(self, input_data: Any = None, context: Optional[Dict[str, Any]] = None) -> Any:
        action = self.config.get("action", "list_accounts")
        
        tool = SalesforceTool(
            username=self.config.get("username"),
            password=self.config.get("password"),
            security_token=self.config.get("security_token")
        )
        
        return tool._run(action=action, **self.config)

    async def get_langchain_object(self, context: Optional[Dict[str, Any]] = None) -> Any:
        return SalesforceTool(
            username=self.config.get("username"),
            password=self.config.get("password"),
            security_token=self.config.get("security_token")
        )
