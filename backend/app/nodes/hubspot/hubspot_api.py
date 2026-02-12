import json
from typing import Any, Dict, Optional
from pydantic import Field
from app.nodes.base import BaseNode, NodeConfig
from app.nodes.registry import register_node
import aiohttp

class HubSpotConfig(NodeConfig):
    endpoint: str = Field("/crm/v3/objects/contacts", description="API Endpoint (e.g., /crm/v3/objects/contacts)")
    method: str = Field("POST", description="HTTP Method (GET, POST, PATCH, DELETE)")
    credentials_id: Optional[str] = Field(None, description="HubSpot Private App Access Token ID")

@register_node("hubspot_node")
class HubSpotNode(BaseNode):
    async def execute(self, input_data: Any, context: Optional[Dict[str, Any]] = None) -> Any:
        endpoint = self.get_config("endpoint")
        method = self.get_config("method", "POST")
        
        creds_data = await self.get_credential("credentials_id")
        access_token = creds_data.get("token") or creds_data.get("access_token") if creds_data else None
        
        if not access_token:
            return {"error": "HubSpot Access Token is required."}
            
        url = f"https://api.hubapi.com{endpoint}"
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }
        
        payload = input_data if isinstance(input_data, dict) else {}

        async with aiohttp.ClientSession() as session:
            async with session.request(method, url, headers=headers, json=payload if method != "GET" else None) as response:
                if response.status >= 400:
                    text = await response.text()
                    try:
                        error_json = json.loads(text)
                        return {"error": f"HubSpot Error {response.status}", "details": error_json}
                    except:
                        return {"error": f"HubSpot Error {response.status}: {text}"}
                
                return await response.json()
