from typing import Any, Dict, Optional
from pydantic import Field
from app.nodes.base import BaseNode, NodeConfig
from app.nodes.registry import register_node
try:
    from simple_salesforce import Salesforce
except ImportError:
    Salesforce = None

class SalesforceConfig(NodeConfig):
    username: Optional[str] = Field(None, description="Salesforce Username")
    password: Optional[str] = Field(None, description="Salesforce Password")
    security_token: Optional[str] = Field(None, description="Salesforce Security Token")
    domain: str = Field("login", description="login (production) or test (sandbox)")
    credentials_id: Optional[str] = Field(None, description="Salesforce Credentials ID")
    object_type: str = Field("Lead", description="Target Object Type (Lead, Contact, Account, Task)")

@register_node("salesforce_node")
class SalesforceNode(BaseNode):
    node_id = "salesforce_node"
    config_model = SalesforceConfig

    async def execute(self, input_data: Any, context: Optional[Dict[str, Any]] = None) -> Any:
        if not Salesforce:
            return {"error": "simple-salesforce library not installed."}

        # 1. Auth Retrieval
        creds = await self.get_credential("credentials_id")
        
        username = creds.get("username") if creds else self.get_config("username")
        password = creds.get("password") if creds else self.get_config("password")
        token = creds.get("security_token") if creds else self.get_config("security_token")
        domain = self.get_config("domain")

        if not username or not password or not token:
            return {"error": "Salesforce Credentials (Username, Password, Token) are required."}

        try:
            # simple-salesforce is sync, but we use it within our execute method
            sf = Salesforce(username=username, password=password, security_token=token, domain=domain)
            obj_type = self.get_config("object_type")
            
            # Simple Create Implementation
            if isinstance(input_data, dict):
                # Using dynamic attribute access for the object type
                res = sf.__getattr__(obj_type).create(input_data)
                return {"status": "success", "id": res.get("id"), "object": obj_type}
            
            return {"error": "Input data must be a dictionary map of field names to values."}
            
        except Exception as e:
            return {"error": f"Salesforce API Failure: {str(e)}"}
