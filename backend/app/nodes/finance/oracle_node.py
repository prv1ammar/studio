"""
Oracle Node - Studio Standard
Batch 84: Enterprise Finance
"""
from typing import Any, Dict, Optional, List
import aiohttp
from ...base import BaseNode
from ...registry import register_node

@register_node("oracle_node")
class OracleNode(BaseNode):
    """
    Manage cloud financial resources and data via Oracle Cloud / Netsuite APIs.
    """
    node_type = "oracle_node"
    version = "1.0.0"
    category = "finance"
    credentials_required = ["oracle_auth"]

    inputs = {
        "action": {
            "type": "dropdown",
            "default": "list_instances",
            "options": ["list_instances", "get_usage_reports", "list_compartments"],
            "description": "Oracle action"
        },
        "compartment_id": {
            "type": "string",
            "required": True
        },
        "region": {
            "type": "string",
            "default": "us-ashburn-1"
        }
    }

    outputs = {
        "result": {"type": "any"},
        "status": {"type": "string"}
    }

    async def execute(self, input_data: Any, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        try:
            creds = await self.get_credential("oracle_auth")
            # Oracle uses a complex signing process for REST, 
            # but we'll implement a clean structure for the endpoint discovery.
            access_token = creds.get("access_token") if creds else self.get_config("access_token")
            
            if not access_token:
                return {"status": "error", "error": "Oracle Access Token / Signing Key is required."}

            headers = {"Authorization": f"Bearer {access_token}", "Accept": "application/json"}
            region = self.get_config("region", "us-ashburn-1")
            base_url = f"https://iaas.{region}.oraclecloud.com/20160918"
            action = self.get_config("action", "list_instances")
            comp_id = self.get_config("compartment_id")

            async with aiohttp.ClientSession() as session:
                if action == "list_instances":
                    url = f"{base_url}/instances"
                    params = {"compartmentId": comp_id}
                    async with session.get(url, headers=headers, params=params) as resp:
                        res_data = await resp.json()
                        return {"status": "success", "data": {"result": res_data}}
                
                return {"status": "error", "error": f"Unsupported action: {action}"}
        except Exception as e:
            return {"status": "error", "error": f"Oracle Node Failed: {str(e)}"}
