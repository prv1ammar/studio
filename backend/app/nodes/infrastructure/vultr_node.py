"""
Vultr Node - Studio Standard
Batch 66: DevOps & Cloud Infrastructure
"""
from typing import Any, Dict, Optional, List
import aiohttp
from ...base import BaseNode
from ...registry import register_node

@register_node("vultr_node")
class VultrNode(BaseNode):
    """
    Automate Vultr cloud infrastructure (Instances, Account, Plans).
    """
    node_type = "vultr_node"
    version = "1.0.0"
    category = "infrastructure"
    credentials_required = ["vultr_auth"]

    inputs = {
        "action": {
            "type": "dropdown",
            "default": "list_instances",
            "options": ["list_instances", "get_account", "list_plans", "create_instance"],
            "description": "Vultr action"
        },
        "label": {
            "type": "string",
            "optional": True,
            "description": "Instance label"
        },
        "region": {
            "type": "string",
            "default": "ewr"
        },
        "plan": {
            "type": "string",
            "default": "vc2-1c-1gb"
        },
        "os_id": {
            "type": "number",
            "default": 387 # Ubuntu 20.04
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
            creds = await self.get_credential("vultr_auth")
            api_key = creds.get("api_key") if creds else self.get_config("api_key")
            
            if not api_key:
                return {"status": "error", "error": "Vultr API Key is required."}

            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            }
            
            base_url = "https://api.vultr.com/v2"
            action = self.get_config("action", "list_instances")

            async with aiohttp.ClientSession() as session:
                if action == "list_instances":
                    async with session.get(f"{base_url}/instances", headers=headers) as resp:
                        res_data = await resp.json()
                        instances = res_data.get("instances", [])
                        return {"status": "success", "data": {"result": instances, "count": len(instances)}}

                elif action == "get_account":
                    async with session.get(f"{base_url}/account", headers=headers) as resp:
                        res_data = await resp.json()
                        return {"status": "success", "data": {"result": res_data.get("account")}}

                elif action == "list_plans":
                    async with session.get(f"{base_url}/plans", headers=headers) as resp:
                        res_data = await resp.json()
                        plans = res_data.get("plans", [])
                        return {"status": "success", "data": {"result": plans, "count": len(plans)}}

                elif action == "create_instance":
                    label = self.get_config("label") or str(input_data)
                    payload = {
                        "region": self.get_config("region"),
                        "plan": self.get_config("plan"),
                        "os_id": int(self.get_config("os_id")),
                        "label": label
                    }
                    async with session.post(f"{base_url}/instances", headers=headers, json=payload) as resp:
                        res_data = await resp.json()
                        return {"status": "success", "data": {"result": res_data.get("instance"), "status": "pending"}}

                return {"status": "error", "error": f"Unsupported action: {action}"}

        except Exception as e:
            return {"status": "error", "error": f"Vultr Node Failed: {str(e)}"}
