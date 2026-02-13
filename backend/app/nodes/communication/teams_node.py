"""
Microsoft Teams Node - Studio Standard (Universal Method)
Batch 89: Core Workflow Nodes
"""
from typing import Any, Dict, Optional, List
import aiohttp
from ...base import BaseNode
from ...registry import register_node

@register_node("teams_node")
class TeamsNode(BaseNode):
    """
    Send messages and manage channels in Microsoft Teams via Graph API.
    """
    node_type = "teams_node"
    version = "1.0.0"
    category = "communication"
    credentials_required = ["teams_auth"]

    inputs = {
        "action": {
            "type": "dropdown",
            "default": "send_message",
            "options": ["send_message", "list_channels", "list_teams", "create_channel"],
            "description": "Teams action"
        },
        "team_id": {
            "type": "string",
            "optional": True
        },
        "channel_id": {
            "type": "string",
            "optional": True
        },
        "message": {
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
            # 1. Authentication (OAuth 2.0)
            creds = await self.get_credential("teams_auth")
            access_token = creds.get("access_token")
            
            if not access_token:
                return {"status": "error", "error": "Microsoft Teams Access Token required."}

            headers = {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json"
            }
            
            # 2. Connect to Real API (Microsoft Graph)
            base_url = "https://graph.microsoft.com/v1.0"
            action = self.get_config("action", "send_message")

            async with aiohttp.ClientSession() as session:
                if action == "send_message":
                    team_id = self.get_config("team_id")
                    channel_id = self.get_config("channel_id")
                    message = self.get_config("message") or str(input_data)
                    
                    if not team_id or not channel_id:
                        return {"status": "error", "error": "team_id and channel_id required"}
                    
                    url = f"{base_url}/teams/{team_id}/channels/{channel_id}/messages"
                    payload = {
                        "body": {
                            "content": message
                        }
                    }
                    async with session.post(url, headers=headers, json=payload) as resp:
                        if resp.status not in [200, 201]:
                            return {"status": "error", "error": f"Teams API Error: {resp.status}"}
                        res_data = await resp.json()
                        return {"status": "success", "data": {"result": res_data}}

                elif action == "list_teams":
                    url = f"{base_url}/me/joinedTeams"
                    async with session.get(url, headers=headers) as resp:
                        if resp.status != 200:
                            return {"status": "error", "error": f"Teams API Error: {resp.status}"}
                        res_data = await resp.json()
                        return {"status": "success", "data": {"result": res_data.get("value", [])}}

                elif action == "list_channels":
                    team_id = self.get_config("team_id")
                    if not team_id:
                        return {"status": "error", "error": "team_id required"}
                    
                    url = f"{base_url}/teams/{team_id}/channels"
                    async with session.get(url, headers=headers) as resp:
                        if resp.status != 200:
                            return {"status": "error", "error": f"Teams API Error: {resp.status}"}
                        res_data = await resp.json()
                        return {"status": "success", "data": {"result": res_data.get("value", [])}}

                return {"status": "error", "error": f"Unsupported action: {action}"}

        except Exception as e:
            return {"status": "error", "error": f"Teams Node Failed: {str(e)}"}
