"""
Zapier NLA Node - Studio Standard (Universal Method)
Batch 101: Automation Bridges (Interoperability)
"""
from typing import Any, Dict, Optional, List
import aiohttp
from ..base import BaseNode
from ..registry import register_node

@register_node("zapier_nla_node")
class ZapierNLANode(BaseNode):
    """
    Execute Zapier actions via Natural Language Actions (NLA) API.
    A bridge to 5,000+ Zapier apps.
    """
    node_type = "zapier_nla_node"
    version = "1.0.0"
    category = "bridges"
    credentials_required = ["zapier_nla_auth"]


    properties = [
        {
            'displayName': 'Action Id',
            'name': 'action_id',
            'type': 'string',
            'default': '',
            'description': 'Action ID from Zapier NLA',
            'required': True,
        },
        {
            'displayName': 'Instructions',
            'name': 'instructions',
            'type': 'string',
            'default': '',
            'description': 'Natural Language input (e.g. 'Send a slack message to @alice saying hello')',
            'required': True,
        },
        {
            'displayName': 'Preview Only',
            'name': 'preview_only',
            'type': 'boolean',
            'default': False,
            'description': 'Preview execution without running?',
        },
    ]
    inputs = {
        "action_id": {
            "type": "string",
            "required": True,
            "description": "Action ID from Zapier NLA"
        },
        "instructions": {
            "type": "string",
            "required": True,
            "description": "Natural Language input (e.g. 'Send a slack message to @alice saying hello')"
        },
        "preview_only": {
            "type": "boolean",
            "default": False,
            "description": "Preview execution without running?"
        }
    }

    outputs = {
        "result": {"type": "any"},
        "status": {"type": "string"}
    }

    async def execute(self, input_data: Any, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        try:
            # 1. Authentication
            creds = await self.get_credential("zapier_nla_auth")
            api_key = creds.get("api_key") # Personal/OAuth Access Token
            
            if not api_key:
                return {"status": "error", "error": "Zapier NLA API Key required."}

            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            }
            
            # 2. Payload
            action_id = self.get_config("action_id")
            instructions = self.get_config("instructions") or str(input_data)
            preview = self.get_config("preview_only", False)
            
            if not action_id:
                return {"status": "error", "error": "action_id required"}
            
            url = f"https://nla.zapier.com/api/v1/exposed/{action_id}/execute"
            
            payload = {
                "instructions": instructions,
                "preview_only": preview
            }
            
            # 3. Connect to Real API
            async with aiohttp.ClientSession() as session:
                async with session.post(url, headers=headers, json=payload) as resp:
                    if resp.status != 200:
                         error_text = await resp.text()
                         return {"status": "error", "error": f"Zapier NLA Error: {resp.status} - {error_text}"}
                    
                    res_data = await resp.json()
                    
                    return {
                        "status": "success",
                        "data": {
                            "result": res_data
                        }
                    }

        except Exception as e:
            return {"status": "error", "error": f"Zapier NLA Node Failed: {str(e)}"}