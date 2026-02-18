"""
Jobber Node - Studio Standard
Batch 80: Industrial & Service Ops
"""
from typing import Any, Dict, Optional, List
import aiohttp
from ..base import BaseNode
from ..registry import register_node

@register_node("jobber_node")
class JobberNode(BaseNode):
    """
    Manage quotes, jobs, and invoicing via Jobber API.
    """
    node_type = "jobber_node"
    version = "1.0.0"
    category = "field_service"
    credentials_required = ["jobber_auth"]

    # Jobber uses GraphQL for most things, but we'll provide a simplified REST-like interface
    async def execute(self, input_data: Any, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        try:
            creds = await self.get_credential("jobber_auth")
            access_token = creds.get("access_token")
            
            headers = {"Authorization": f"Bearer {access_token}", "X-Jobber-Graphql-Version": "2023-08-18"}
            url = "https://api.getjobber.com/api/graphql"
            
            # Simple list jobs query
            query = "{ jobs(first: 10) { nodes { id title status } } }"
            payload = {"query": query}
            
            async with aiohttp.ClientSession() as session:
                async with session.post(url, headers=headers, json=payload) as resp:
                    res_data = await resp.json()
                    return {"status": "success", "data": {"result": res_data}}
        except Exception as e:
            return {"status": "error", "error": str(e)}
