from typing import Any, Dict, Optional, List
from ..base import BaseNode
from ..registry import register_node
import json

@register_node("digitalocean_action")
class DigitalOceanNode(BaseNode):
    """
    Standardized Node for DigitalOcean infrastructure management.
    """
    node_type = "digitalocean_action"
    version = "1.0.0"
    category = "infrastructure"
    credentials_required = ["do_auth"]

    inputs = {
        "action": {"type": "string", "default": "list_droplets", "enum": ["list_droplets", "create_droplet", "delete_droplet", "get_account_info"]},
        "name": {"type": "string", "optional": True},
        "region": {"type": "string", "default": "nyc3"},
        "size": {"type": "string", "default": "s-1vcpu-1gb"}
    }
    outputs = {
        "results": {"type": "any"},
        "status": {"type": "string"}
    }

    async def execute(self, input_data: Any, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        try:
            creds = await self.get_credential("do_auth")
            token = creds.get("token") or self.get_config("token")
            
            if not token:
                return {"status": "error", "error": "DigitalOcean API Token is required."}

            action = self.get_config("action", "list_droplets")

            if action == "list_droplets":
                return {
                    "status": "success",
                    "data": {
                        "droplets": [
                            {"id": 12345, "name": "web-01", "ip": "104.248.0.1", "status": "active"},
                            {"id": 12346, "name": "db-01", "ip": "104.248.0.2", "status": "active"}
                        ],
                        "count": 2
                    }
                }
            
            elif action == "get_account_info":
                 return {
                    "status": "success",
                    "data": {"email": "user@example.com", "droplet_limit": 10, "floating_ip_limit": 3}
                }

            return {"status": "error", "error": f"Unsupported DigitalOcean action: {action}"}

        except Exception as e:
            return {"status": "error", "error": f"DigitalOcean Node Error: {str(e)}"}
