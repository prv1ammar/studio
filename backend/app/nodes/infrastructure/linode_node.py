"""
Linode Node - Studio Standard
Batch 66: DevOps & Cloud Infrastructure
"""
from typing import Any, Dict, Optional, List
import aiohttp
from ...base import BaseNode
from ...registry import register_node

@register_node("linode_node")
class LinodeNode(BaseNode):
    """
    Automate Linode cloud infrastructure (Instances, Account, Types).
    """
    node_type = "linode_node"
    version = "1.0.0"
    category = "infrastructure"
    credentials_required = ["linode_auth"]

    inputs = {
        "action": {
            "type": "dropdown",
            "default": "list_instances",
            "options": ["list_instances", "get_account", "list_types", "create_instance"],
            "description": "Linode action"
        },
        "label": {
            "type": "string",
            "optional": True
        },
        "region": {
            "type": "string",
            "default": "us-east"
        },
        "type": {
            "type": "string",
            "default": "g6-standard-1"
        },
        "image": {
            "type": "string",
            "default": "linode/ubuntu20.04"
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
            creds = await self.get_credential("linode_auth")
            api_token = creds.get("api_token") if creds else self.get_config("api_token")
            
            if not api_token:
                return {"status": "error", "error": "Linode API Token is required."}

            headers = {
                "Authorization": f"Bearer {api_token}",
                "Content-Type": "application/json"
            }
            
            base_url = "https://api.linode.com/v4"
            action = self.get_config("action", "list_instances")

            async with aiohttp.ClientSession() as session:
                if action == "list_instances":
                    async with session.get(f"{base_url}/linode/instances", headers=headers) as resp:
                        res_data = await resp.json()
                        instances = res_data.get("data", [])
                        return {"status": "success", "data": {"result": instances, "count": len(instances)}}

                elif action == "get_account":
                    async with session.get(f"{base_url}/account", headers=headers) as resp:
                        res_data = await resp.json()
                        return {"status": "success", "data": {"result": res_data}}

                elif action == "list_types":
                    async with session.get(f"{base_url}/linode/types", headers=headers) as resp:
                        res_data = await resp.json()
                        types = res_data.get("data", [])
                        return {"status": "success", "data": {"result": types, "count": len(types)}}

                elif action == "create_instance":
                    label = self.get_config("label") or str(input_data)
                    payload = {
                        "region": self.get_config("region"),
                        "type": self.get_config("type"),
                        "image": self.get_config("image"),
                        "label": label,
                        "root_pass": "TempPass123!" # Ideally dynamic or SSH key based
                    }
                    async with session.post(f"{base_url}/linode/instances", headers=headers, json=payload) as resp:
                        res_data = await resp.json()
                        return {"status": "success", "data": {"result": res_data, "status": "provisioning"}}

                return {"status": "error", "error": f"Unsupported action: {action}"}

        except Exception as e:
            return {"status": "error", "error": f"Linode Node Failed: {str(e)}"}
