"""
Sprout Social Node - Studio Standard (Universal Method)
Batch 106: Social Media
"""
from typing import Any, Dict, Optional
import aiohttp
from ...base import BaseNode
from ...registry import register_node

@register_node("sprout_social_node")
class SproutSocialNode(BaseNode):
    """
    Sprout Social integration for enterprise social media.
    """
    node_type = "sprout_social_node"
    version = "1.0.0"
    category = "social_media"
    credentials_required = ["sprout_social_auth"]

    inputs = {
        "action": {
            "type": "dropdown",
            "default": "get_customer_metrics",
            "options": ["get_customer_metrics", "get_metadata"],
            "description": "Sprout Social action"
        },
        "customer_id": {
            "type": "string",
            "optional": True
        }
    }

    outputs = {
        "result": {"type": "any"},
        "status": {"type": "string"}
    }

    async def execute(self, input_data: Any, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        try:
            creds = await self.get_credential("sprout_social_auth")
            access_token = creds.get("access_token")
            
            if not access_token:
                return {"status": "error", "error": "Sprout Social access token required"}

            base_url = "https://api.sproutsocial.com/v1"
            headers = {"Authorization": f"Bearer {access_token}"}
            
            action = self.get_config("action", "get_customer_metrics")

            async with aiohttp.ClientSession() as session:
                if action == "get_customer_metrics":
                    customer_id = self.get_config("customer_id")
                    if not customer_id:
                        # Try to fetch default customer ID if not provided, or fail
                        pass
                    
                    if not customer_id:
                         return {"status": "error", "error": "customer_id required"}

                    url = f"{base_url}/{customer_id}/analytics/profiles"
                    params = {"metrics": "impressions,engagements"}
                    
                    async with session.get(url, headers=headers, params=params) as resp:
                        if resp.status != 200:
                             error_text = await resp.text()
                             # Sprout API typically robust, handling errors here
                             return {"status": "error", "error": f"Sprout Social API Error {resp.status}: {error_text}"}
                        res_data = await resp.json()
                        return {"status": "success", "data": {"result": res_data}}
                
                elif action == "get_metadata":
                    url = f"{base_url}/metadata/customer"
                    async with session.get(url, headers=headers) as resp:
                        res_data = await resp.json()
                        return {"status": "success", "data": {"result": res_data}}

            return {"status": "error", "error": f"Unsupported action: {action}"}

        except Exception as e:
            return {"status": "error", "error": f"Sprout Social Node Failed: {str(e)}"}
