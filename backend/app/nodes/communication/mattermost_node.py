"""
Mattermost Node - Studio Standard (Universal Method)
Batch 104: Communication Essentials
"""
from typing import Any, Dict, Optional
import aiohttp
from ...base import BaseNode
from ...registry import register_node

@register_node("mattermost_node")
class MattermostNode(BaseNode):
    """
    Mattermost self-hosted team chat integration.
    """
    node_type = "mattermost_node"
    version = "1.0.0"
    category = "communication"
    credentials_required = ["mattermost_auth"]

    inputs = {
        "action": {
            "type": "dropdown",
            "default": "send_message",
            "options": ["send_message", "create_channel", "list_channels", "list_teams", "add_user_to_channel"],
            "description": "Mattermost action"
        },
        "channel_id": {
            "type": "string",
            "optional": True
        },
        "message": {
            "type": "string",
            "optional": True
        },
        "channel_name": {
            "type": "string",
            "optional": True
        },
        "team_id": {
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
            creds = await self.get_credential("mattermost_auth")
            server_url = creds.get("server_url")
            access_token = creds.get("access_token")
            
            if not server_url or not access_token:
                return {"status": "error", "error": "Mattermost server URL and access token required"}

            base_url = f"{server_url.rstrip('/')}/api/v4"
            headers = {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json"
            }
            
            action = self.get_config("action", "send_message")

            async with aiohttp.ClientSession() as session:
                if action == "send_message":
                    channel_id = self.get_config("channel_id")
                    message = self.get_config("message") or str(input_data)
                    
                    if not channel_id or not message:
                        return {"status": "error", "error": "channel_id and message required"}
                    
                    url = f"{base_url}/posts"
                    payload = {
                        "channel_id": channel_id,
                        "message": message
                    }
                    
                    async with session.post(url, headers=headers, json=payload) as resp:
                        if resp.status not in [200, 201]:
                            error_text = await resp.text()
                            return {"status": "error", "error": f"Mattermost API Error {resp.status}: {error_text}"}
                        res_data = await resp.json()
                        return {"status": "success", "data": {"result": res_data}}

                elif action == "list_teams":
                    url = f"{base_url}/users/me/teams"
                    async with session.get(url, headers=headers) as resp:
                        if resp.status != 200:
                            error_text = await resp.text()
                            return {"status": "error", "error": f"Mattermost API Error {resp.status}: {error_text}"}
                        res_data = await resp.json()
                        return {"status": "success", "data": {"result": res_data}}

                elif action == "list_channels":
                    team_id = self.get_config("team_id")
                    if not team_id:
                        return {"status": "error", "error": "team_id required"}
                    
                    url = f"{base_url}/users/me/teams/{team_id}/channels"
                    async with session.get(url, headers=headers) as resp:
                        if resp.status != 200:
                            error_text = await resp.text()
                            return {"status": "error", "error": f"Mattermost API Error {resp.status}: {error_text}"}
                        res_data = await resp.json()
                        return {"status": "success", "data": {"result": res_data}}

                return {"status": "error", "error": f"Unsupported action: {action}"}

        except Exception as e:
            return {"status": "error", "error": f"Mattermost Node Failed: {str(e)}"}
