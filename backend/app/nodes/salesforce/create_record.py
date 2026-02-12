from typing import Any, Dict, Optional
from pydantic import Field
from app.nodes.base import BaseNode, NodeConfig
from app.nodes.registry import register_node
import aiohttp

class SalesforceConfig(NodeConfig):
    instance_url: str = Field(..., description="Salesforce Instance URL (e.g. https://mycompany.my.salesforce.com)")
    access_token: str = Field(..., description="OAuth Access Token")

@register_node("salesforce_node")
class SalesforceNode(BaseNode):
    node_id = "salesforce_node"
    node_type = "Salesforce"
    label = "Create Record"
    config_model = SalesforceConfig

    async def execute(self, input_data: Any, context: Optional[Dict[str, Any]] = None) -> Any:
        instance_url = self.get_config("instance_url")
        token = self.get_config("access_token")
        
        sobject = input_data.get("sobject", "Lead") if isinstance(input_data, dict) else "Lead"
        data = input_data.get("data", input_data)
        
        url = f"{instance_url}/services/data/v58.0/sobjects/{sobject}"
        headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
        
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=data, headers=headers) as response:
                if response.status >= 400:
                    return {"error": await response.text()}
                return await response.json()
