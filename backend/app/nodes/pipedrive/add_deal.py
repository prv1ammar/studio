from typing import Any, Dict, Optional
from pydantic import Field
from app.nodes.base import BaseNode, NodeConfig
from app.nodes.registry import register_node
import aiohttp

class PipedriveConfig(NodeConfig):
    api_token: str = Field(..., description="Pipedrive API Token")
    company_domain: str = Field(..., description="Company Domain (e.g. company.pipedrive.com)")

@register_node("pipedrive_node")
class PipedriveNode(BaseNode):
    node_id = "pipedrive_node"
    node_type = "Pipedrive"
    label = "Add Deal"
    config_model = PipedriveConfig

    async def execute(self, input_data: Any, context: Optional[Dict[str, Any]] = None) -> Any:
        token = self.get_config("api_token")
        domain = self.get_config("company_domain")
        
        url = f"https://{domain}.pipedrive.com/v1/deals?api_token={token}"
        
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=input_data) as response:
                result = await response.json()
                if not result.get("success"):
                    return {"error": result.get("error")}
                return result.get("data")
