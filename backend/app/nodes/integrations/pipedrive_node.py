import aiohttp
from typing import Any, Dict, Optional
from pydantic import Field
from app.nodes.base import BaseNode, NodeConfig
from app.nodes.registry import register_node

class PipedriveConfig(NodeConfig):
    api_token: Optional[str] = Field(None, description="Pipedrive API Token")
    company_domain: Optional[str] = Field(None, description="Company Domain (e.g. yourcompany)")
    credentials_id: Optional[str] = Field(None, description="Pipedrive Credentials ID")
    action: str = Field("create_person", description="Action to perform (create_person, create_deal)")

@register_node("pipedrive_node")
class PipedriveNode(BaseNode):
    node_id = "pipedrive_node"
    config_model = PipedriveConfig

    async def execute(self, input_data: Any, context: Optional[Dict[str, Any]] = None) -> Any:
        # 1. Auth Retrieval
        creds = await self.get_credential("credentials_id")
        token = creds.get("api_token") if creds else self.get_config("api_token")
        domain = self.get_config("company_domain")

        if not token or not domain:
            return {"error": "Pipedrive API Token and Company Domain are required."}

        action = self.get_config("action")
        base_url = f"https://{domain}.pipedrive.com/api/v1"

        async with aiohttp.ClientSession() as session:
            try:
                if action == "create_person":
                    url = f"{base_url}/persons?api_token={token}"
                    payload = input_data if isinstance(input_data, dict) else {"name": str(input_data)}
                    async with session.post(url, json=payload) as resp:
                        result = await resp.json()
                        if not result.get("success"):
                            return {"error": f"Pipedrive Error: {result.get('error')}"}
                        return {"status": "success", "id": result["data"]["id"], "type": "person"}

                elif action == "create_deal":
                    url = f"{base_url}/deals?api_token={token}"
                    payload = input_data if isinstance(input_data, dict) else {"title": str(input_data)}
                    async with session.post(url, json=payload) as resp:
                        result = await resp.json()
                        if not result.get("success"):
                            return {"error": f"Pipedrive Error: {result.get('error')}"}
                        return {"status": "success", "id": result["data"]["id"], "type": "deal"}

                return {"error": f"Unsupported Pipedrive action: {action}"}

            except Exception as e:
                return {"error": f"Pipedrive Node Failed: {str(e)}"}
