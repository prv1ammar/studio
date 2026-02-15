"""
Cloudflare Node - Studio Standard (Universal Method)
Batch 113: Intelligent Infrastructure & IoT
"""
from typing import Any, Dict, Optional
import aiohttp
from ...base import BaseNode
from ...registry import register_node

@register_node("cloudflare_node")
class CloudflareNode(BaseNode):
    """
    Manage Cloudflare settings (DNS, Workers, etc.).
    """
    node_type = "cloudflare_node"
    version = "1.0.0"
    category = "infrastructure"
    credentials_required = ["cloudflare_auth"]

    inputs = {
        "action": {
            "type": "dropdown",
            "default": "list_zones",
            "options": ["list_zones", "get_dns_records", "create_dns_record", "purge_cache"],
            "description": "Cloudflare action to perform"
        },
        "zone_id": {
            "type": "string",
            "optional": True,
            "description": "Cloudflare Zone ID"
        },
        "dns_name": {
            "type": "string",
            "optional": True,
            "description": "Record name (e.g., example.com)"
        }
    }

    outputs = {
        "result": {"type": "any"},
        "status": {"type": "string"}
    }

    async def execute(self, input_data: Any, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        try:
            creds = await self.get_credential("cloudflare_auth")
            api_token = creds.get("api_token")
            
            if not api_token:
                return {"status": "error", "error": "Cloudflare API Token is required"}

            action = self.get_config("action", "list_zones")
            zone_id = self.get_config("zone_id")
            
            base_url = "https://api.cloudflare.com/client/v4"
            headers = {
                "Authorization": f"Bearer {api_token}",
                "Content-Type": "application/json"
            }

            async with aiohttp.ClientSession() as session:
                if action == "list_zones":
                    async with session.get(f"{base_url}/zones", headers=headers) as response:
                        data = await response.json()
                        return {"status": "success", "data": {"result": data.get("result", [])}}

                elif action == "get_dns_records":
                    if not zone_id: return {"status": "error", "error": "Zone ID required"}
                    async with session.get(f"{base_url}/zones/{zone_id}/dns_records", headers=headers) as response:
                        data = await response.json()
                        return {"status": "success", "data": {"result": data.get("result", [])}}

                elif action == "purge_cache":
                    if not zone_id: return {"status": "error", "error": "Zone ID required"}
                    payload = {"purge_everything": True}
                    async with session.post(f"{base_url}/zones/{zone_id}/purge_cache", headers=headers, json=payload) as response:
                        data = await response.json()
                        return {"status": "success", "data": {"result": data.get("result", {})}}

            return {"status": "error", "error": f"Unsupported action: {action}"}

        except Exception as e:
            return {"status": "error", "error": f"Cloudflare API failed: {str(e)}"}
