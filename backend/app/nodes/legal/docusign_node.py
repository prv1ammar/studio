"""
DocuSign Node - Studio Standard
Batch 67: Legal & Compliance
"""
from typing import Any, Dict, Optional, List
import aiohttp
from ...base import BaseNode
from ...registry import register_node

@register_node("docusign_node")
class DocuSignNode(BaseNode):
    """
    Automate e-signatures and document templates via DocuSign eSignature API.
    """
    node_type = "docusign_node"
    version = "1.0.0"
    category = "legal"
    credentials_required = ["docusign_auth"]

    inputs = {
        "action": {
            "type": "dropdown",
            "default": "list_envelopes",
            "options": ["list_envelopes", "get_envelope", "list_templates", "create_envelope"],
            "description": "DocuSign action"
        },
        "account_id": {
            "type": "string",
            "required": True,
            "description": "DocuSign Account ID"
        },
        "envelope_id": {
            "type": "string",
            "optional": True
        },
        "template_id": {
            "type": "string",
            "optional": True
        },
        "base_url": {
            "type": "string",
            "default": "https://demo.docusign.net/restapi/v2.1",
            "description": "API Base URL (e.g. demo vs production)"
        }
    }

    outputs = {
        "result": {"type": "any"},
        "status": {"type": "string"},
        "count": {"type": "number"}
    }

    async def execute(self, input_data: Any, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        try:
            creds = await self.get_credential("docusign_auth")
            access_token = creds.get("access_token") if creds else self.get_config("access_token")
            
            if not access_token:
                return {"status": "error", "error": "DocuSign Access Token is required."}

            headers = {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json",
                "Accept": "application/json"
            }
            
            base_url = self.get_config("base_url").rstrip("/")
            account_id = self.get_config("account_id")
            action = self.get_config("action", "list_envelopes")

            async with aiohttp.ClientSession() as session:
                if action == "list_envelopes":
                    # Requires from_date filter usually
                    url = f"{base_url}/accounts/{account_id}/envelopes"
                    params = {"from_date": "2024-01-01"} 
                    async with session.get(url, headers=headers, params=params) as resp:
                        res_data = await resp.json()
                        envelopes = res_data.get("envelopes", [])
                        return {"status": "success", "data": {"result": envelopes, "count": len(envelopes)}}

                elif action == "get_envelope":
                    env_id = self.get_config("envelope_id") or str(input_data)
                    url = f"{base_url}/accounts/{account_id}/envelopes/{env_id}"
                    async with session.get(url, headers=headers) as resp:
                        res_data = await resp.json()
                        return {"status": "success", "data": {"result": res_data}}

                elif action == "list_templates":
                    url = f"{base_url}/accounts/{account_id}/templates"
                    async with session.get(url, headers=headers) as resp:
                        res_data = await resp.json()
                        templates = res_data.get("envelopeTemplates", [])
                        return {"status": "success", "data": {"result": templates, "count": len(templates)}}

                return {"status": "error", "error": f"Unsupported DocuSign action: {action}"}

        except Exception as e:
            return {"status": "error", "error": f"DocuSign Node Failed: {str(e)}"}
