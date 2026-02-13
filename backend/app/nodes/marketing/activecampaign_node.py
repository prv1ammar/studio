"""
ActiveCampaign Node - Studio Standard (Universal Method)
Batch 90: CRM & Marketing (n8n Critical)
"""
from typing import Any, Dict, Optional, List
import aiohttp
from ...base import BaseNode
from ...registry import register_node

@register_node("activecampaign_node")
class ActiveCampaignNode(BaseNode):
    """
    Manage contacts, deals, and campaigns in ActiveCampaign.
    """
    node_type = "activecampaign_node"
    version = "1.0.0"
    category = "marketing"
    credentials_required = ["activecampaign_auth"]

    inputs = {
        "action": {
            "type": "dropdown",
            "default": "create_contact",
            "options": ["create_contact", "update_contact", "list_contacts", "create_deal", "list_campaigns"],
            "description": "ActiveCampaign action"
        },
        "email": {
            "type": "string",
            "optional": True
        },
        "first_name": {
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
            # 1. Authentication
            creds = await self.get_credential("activecampaign_auth")
            api_key = creds.get("api_key")
            account_name = creds.get("account_name")
            
            if not api_key or not account_name:
                return {"status": "error", "error": "ActiveCampaign API Key and Account Name required."}

            headers = {
                "Api-Token": api_key,
                "Content-Type": "application/json"
            }
            
            # 2. Connect to Real API
            base_url = f"https://{account_name}.api-us1.com/api/3"
            action = self.get_config("action", "create_contact")

            async with aiohttp.ClientSession() as session:
                if action == "create_contact":
                    email = self.get_config("email") or str(input_data)
                    first_name = self.get_config("first_name", "")
                    
                    url = f"{base_url}/contacts"
                    payload = {
                        "contact": {
                            "email": email,
                            "firstName": first_name
                        }
                    }
                    async with session.post(url, headers=headers, json=payload) as resp:
                        if resp.status not in [200, 201]:
                            return {"status": "error", "error": f"ActiveCampaign Error: {resp.status}"}
                        res_data = await resp.json()
                        return {"status": "success", "data": {"result": res_data.get("contact", {})}}

                elif action == "list_contacts":
                    url = f"{base_url}/contacts"
                    async with session.get(url, headers=headers) as resp:
                        if resp.status != 200:
                            return {"status": "error", "error": f"ActiveCampaign Error: {resp.status}"}
                        res_data = await resp.json()
                        return {"status": "success", "data": {"result": res_data.get("contacts", [])}}

                elif action == "list_campaigns":
                    url = f"{base_url}/campaigns"
                    async with session.get(url, headers=headers) as resp:
                        if resp.status != 200:
                            return {"status": "error", "error": f"ActiveCampaign Error: {resp.status}"}
                        res_data = await resp.json()
                        return {"status": "success", "data": {"result": res_data.get("campaigns", [])}}

                return {"status": "error", "error": f"Unsupported action: {action}"}

        except Exception as e:
            return {"status": "error", "error": f"ActiveCampaign Node Failed: {str(e)}"}
