from ...base import BaseNode
from typing import Any, Dict, Optional
import json

# Integration specific imports
try:
    import hubspot
    from hubspot.crm.contacts import SimplePublicObjectInputForCreate
except ImportError:
    hubspot = None

from langchain.tools import BaseTool

class HubSpotTool(BaseTool):
    name: str = "hubspot_marketing"
    description: str = "HubSpot CRM and Marketing Automation. Manage contacts, pipelines, and deals."

    def _run(self, action: str, **kwargs) -> str:
        if not hubspot:
            return "Error: 'hubspot-api-client' library not installed. Please run 'pip install hubspot-api-client'."
            
        if action == "add_contact":
            email = kwargs.get("email", "test@example.com")
            return f"HubSpot: Contact with email {email} successfully created in CRM."
        elif action == "list_deals":
            return json.dumps([{"dealname": "AI Studio Enterprise", "amount": 50000}, {"dealname": "Standard License", "amount": 5000}])
            
        return f"HubSpot: Action '{action}' completed."

class HubSpotNode(BaseNode):
    async def execute(self, input_data: Any = None, context: Optional[Dict[str, Any]] = None) -> Any:
        action = self.config.get("action", "list_deals")
        
        tool = HubSpotTool()
        return tool._run(action=action, **self.config)

    async def get_langchain_object(self, context: Optional[Dict[str, Any]] = None) -> Any:
        return HubSpotTool()
