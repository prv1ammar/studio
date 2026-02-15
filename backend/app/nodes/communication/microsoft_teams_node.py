"""
Microsoft Teams Node - Studio Standard (Universal Method)
Batch 104: Communication Essentials
"""
from typing import Any, Dict, Optional
import aiohttp
from ...base import BaseNode
from ...registry import register_node

@register_node("microsoft_teams_node")
class MicrosoftTeamsNode(BaseNode):
    """
    Microsoft Teams integration for enterprise communication.
    """
    node_type = "microsoft_teams_node"
    version = "1.0.0"
    category = "communication"
    credentials_required = ["microsoft_teams_auth"]

    inputs = {
        "action": {
            "type": "dropdown",
            "default": "send_message",
            "options": ["send_message", "send_channel_message", "create_channel", "list_channels", "list_teams", "send_adaptive_card"],
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
        },
        "channel_name": {
            "type": "string",
            "optional": True
        },
        "adaptive_card": {
            "type": "string",
            "optional": True,
            "description": "JSON adaptive card"
        }
    }

    outputs = {
        "result": {"type": "any"},
        "status": {"type": "string"}
    }

    async def execute(self, input_data: Any, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        try:
            creds = await self.get_credential("microsoft_teams_auth")
            access_token = creds.get("access_token")
            
            if not access_token:
                return {"status": "error", "error": "Microsoft Teams access token required"}

            base_url = "https://graph.microsoft.com/v1.0"
            headers = {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json"
            }
            
            action = self.get_config("action", "send_message")

            async with aiohttp.ClientSession() as session:
                if action == "send_channel_message":
                    team_id = self.get_config("team_id")
                    channel_id = self.get_config("channel_id")
                    message = self.get_config("message") or str(input_data)
                    
                    if not all([team_id, channel_id, message]):
                        return {"status": "error", "error": "team_id, channel_id, and message required"}
                    
                    url = f"{base_url}/teams/{team_id}/channels/{channel_id}/messages"
                    payload = {
                        "body": {
                            "content": message
                        }
                    }
                    
                    async with session.post(url, headers=headers, json=payload) as resp:
                        if resp.status not in [200, 201]:
                            error_text = await resp.text()
                            return {"status": "error", "error": f"Teams API Error {resp.status}: {error_text}"}
                        res_data = await resp.json()
                        return {"status": "success", "data": {"result": res_data}}

                elif action == "list_teams":
                    url = f"{base_url}/me/joinedTeams"
                    async with session.get(url, headers=headers) as resp:
                        if resp.status != 200:
                            error_text = await resp.text()
                            return {"status": "error", "error": f"Teams API Error {resp.status}: {error_text}"}
                        res_data = await resp.json()
                        return {"status": "success", "data": {"result": res_data.get("value", [])}}

                elif action == "list_channels":
                    team_id = self.get_config("team_id")
                    if not team_id:
                        return {"status": "error", "error": "team_id required"}
                    
                    url = f"{base_url}/teams/{team_id}/channels"
                    async with session.get(url, headers=headers) as resp:
                        if resp.status != 200:
                            error_text = await resp.text()
                            return {"status": "error", "error": f"Teams API Error {resp.status}: {error_text}"}
                        res_data = await resp.json()
                        return {"status": "success", "data": {"result": res_data.get("value", [])}}

                elif action == "create_channel":
                    team_id = self.get_config("team_id")
                    channel_name = self.get_config("channel_name")
                    
                    if not all([team_id, channel_name]):
                        return {"status": "error", "error": "team_id and channel_name required"}
                    
                    url = f"{base_url}/teams/{team_id}/channels"
                    payload = {
                        "displayName": channel_name,
                        "membershipType": "standard"
                    }
                    
                    async with session.post(url, headers=headers, json=payload) as resp:
                        if resp.status not in [200, 201]:
                            error_text = await resp.text()
                            return {"status": "error", "error": f"Teams API Error {resp.status}: {error_text}"}
                        res_data = await resp.json()
                        return {"status": "success", "data": {"result": res_data}}

                elif action == "send_adaptive_card":
                    team_id = self.get_config("team_id")
                    channel_id = self.get_config("channel_id")
                    card_json = self.get_config("adaptive_card")
                    
                    if not all([team_id, channel_id, card_json]):
                        return {"status": "error", "error": "team_id, channel_id, and adaptive_card required"}
                    
                    import json
                    card = json.loads(card_json) if isinstance(card_json, str) else card_json
                    
                    url = f"{base_url}/teams/{team_id}/channels/{channel_id}/messages"
                    payload = {
                        "body": {
                            "contentType": "html",
                            "content": "<attachment id=\"1\"></attachment>"
                        },
                        "attachments": [
                            {
                                "id": "1",
                                "contentType": "application/vnd.microsoft.card.adaptive",
                                "content": card
                            }
                        ]
                    }
                    
                    async with session.post(url, headers=headers, json=payload) as resp:
                        if resp.status not in [200, 201]:
                            error_text = await resp.text()
                            return {"status": "error", "error": f"Teams API Error {resp.status}: {error_text}"}
                        res_data = await resp.json()
                        return {"status": "success", "data": {"result": res_data}}

                return {"status": "error", "error": f"Unsupported action: {action}"}

        except Exception as e:
            return {"status": "error", "error": f"Microsoft Teams Node Failed: {str(e)}"}
