"""
NewRelic Node - Studio Standard
Batch 83: Observability & SRE
"""
from typing import Any, Dict, Optional, List
import aiohttp
from ..base import BaseNode
from ..registry import register_node

@register_node("newrelic_node")
class NewRelicNode(BaseNode):
    """
    Access APM performance data and alerts via the New Relic GraphiQL or REST API.
    """
    node_type = "newrelic_node"
    version = "1.0.0"
    category = "observability"
    credentials_required = ["newrelic_auth"]

    async def execute(self, input_data: Any, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        try:
            creds = await self.get_credential("newrelic_auth")
            api_key = creds.get("api_key")
            
            # New Relic GraphQL NerdGraph API
            url = "https://api.newrelic.com/graphql"
            headers = {"Api-Key": api_key, "Content-Type": "application/json"}
            
            # Simple query to get account info and entities
            query = "{ actor { accounts { name id } entitySearch(query: \"domain = 'APM'\") { results { entities { name guid } } } } }"
            payload = {"query": query}
            
            async with aiohttp.ClientSession() as session:
                async with session.post(url, headers=headers, json=payload) as resp:
                    res_data = await resp.json()
                    return {"status": "success", "data": {"result": res_data}}
        except Exception as e:
            return {"status": "error", "error": f"NewRelic Node Failed: {str(e)}"}
