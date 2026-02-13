"""
DigitalOcean Node - Studio Standard
Batch 66: DevOps & Cloud Infrastructure
"""
from typing import Any, Dict, Optional, List
import aiohttp
from ...base import BaseNode
from ...registry import register_node

@register_node("digitalocean_node")
class DigitalOceanNode(BaseNode):
    """
    Automate DigitalOcean infrastructure management (Droplets, Account, Images).
    """
    node_type = "digitalocean_node"
    version = "1.1.0"
    category = "infrastructure"
    credentials_required = ["do_auth"]

    inputs = {
        "action": {
            "type": "dropdown",
            "default": "list_droplets",
            "options": ["list_droplets", "get_account", "list_images", "create_droplet"],
            "description": "DigitalOcean action"
        },
        "name": {
            "type": "string",
            "optional": True,
            "description": "Droplet name"
        },
        "region": {
            "type": "string",
            "default": "nyc3"
        },
        "size": {
            "type": "string",
            "default": "s-1vcpu-1gb"
        },
        "image": {
            "type": "string",
            "default": "ubuntu-20-04-x64"
        }
    }

    outputs = {
        "result": {"type": "any"},
        "status": {"type": "string"},
        "count": {"type": "number"}
    }

    async def execute(self, input_data: Any, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        try:
            # 1. Resolve Auth
            creds = await self.get_credential("do_auth")
            token = creds.get("token") if creds else self.get_config("token")
            
            if not token:
                return {"status": "error", "error": "DigitalOcean API Token is required."}

            headers = {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json"
            }
            
            base_url = "https://api.digitalocean.com/v2"
            action = self.get_config("action", "list_droplets")

            async with aiohttp.ClientSession() as session:
                if action == "list_droplets":
                    async with session.get(f"{base_url}/droplets", headers=headers) as resp:
                        res_data = await resp.json()
                        droplets = res_data.get("droplets", [])
                        return {"status": "success", "data": {"result": droplets, "count": len(droplets)}}

                elif action == "get_account":
                    async with session.get(f"{base_url}/account", headers=headers) as resp:
                        res_data = await resp.json()
                        return {"status": "success", "data": {"result": res_data.get("account")}}

                elif action == "list_images":
                    async with session.get(f"{base_url}/images", headers=headers) as resp:
                        res_data = await resp.json()
                        images = res_data.get("images", [])
                        return {"status": "success", "data": {"result": images, "count": len(images)}}

                elif action == "create_droplet":
                    name = self.get_config("name") or str(input_data)
                    payload = {
                        "name": name,
                        "region": self.get_config("region"),
                        "size": self.get_config("size"),
                        "image": self.get_config("image")
                    }
                    async with session.post(f"{base_url}/droplets", headers=headers, json=payload) as resp:
                        res_data = await resp.json()
                        return {"status": "success", "data": {"result": res_data.get("droplet"), "status": "creating"}}

                return {"status": "error", "error": f"Unsupported action: {action}"}

        except Exception as e:
            return {"status": "error", "error": f"DigitalOcean Node Failed: {str(e)}"}
