"""
Frame.io Node - Studio Standard
Batch 79: Media Production
"""
from typing import Any, Dict, Optional, List
import aiohttp
from ..base import BaseNode
from ..registry import register_node

@register_node("frameio_node")
class FrameioNode(BaseNode):
    """
    Orchestrate video collaboration, comments, and review links via the Frame.io API.
    """
    node_type = "frameio_node"
    version = "1.0.0"
    category = "media"
    credentials_required = ["frameio_auth"]


    properties = [
        {
            'displayName': 'Operation',
            'name': 'operation',
            'type': 'options',
            'default': 'get_me',
            'options': [
                {'name': 'Get Me', 'value': 'get_me'},
                {'name': 'List Projects', 'value': 'list_projects'},
                {'name': 'List Assets', 'value': 'list_assets'},
                {'name': 'Get Asset Comments', 'value': 'get_asset_comments'},
                {'name': 'Create Comment', 'value': 'create_comment'},
            ],
            'description': 'Frame.io action',
        },
        {
            'displayName': 'Asset Id',
            'name': 'asset_id',
            'type': 'string',
            'default': '',
        },
        {
            'displayName': 'Comment',
            'name': 'comment',
            'type': 'string',
            'default': '',
        },
        {
            'displayName': 'Project Id',
            'name': 'project_id',
            'type': 'string',
            'default': '',
        },
    ]
    inputs = {
        "action": {
            "type": "dropdown",
            "default": "get_me",
            "options": ["get_me", "list_projects", "list_assets", "get_asset_comments", "create_comment"],
            "description": "Frame.io action"
        },
        "project_id": {
            "type": "string",
            "optional": True
        },
        "asset_id": {
            "type": "string",
            "optional": True
        },
        "comment": {
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
            creds = await self.get_credential("frameio_auth")
            access_token = creds.get("access_token") if creds else self.get_config("access_token")
            
            if not access_token:
                return {"status": "error", "error": "Frame.io Bearer Token is required."}

            headers = {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json"
            }
            
            base_url = "https://api.frame.io/v2"
            action = self.get_config("action", "get_me")

            async with aiohttp.ClientSession() as session:
                if action == "get_me":
                    url = f"{base_url}/me"
                    async with session.get(url, headers=headers) as resp:
                        res_data = await resp.json()
                        return {"status": "success", "data": {"result": res_data}}

                elif action == "list_projects":
                    # Note: Frame.io usually needs a TEAM_ID to list projects
                    me_resp = await session.get(f"{base_url}/me", headers=headers)
                    me_data = await me_resp.json()
                    team_id = me_data.get("next_billing_team_id") or me_data.get("default_team_id")
                    
                    if not team_id:
                        return {"status": "error", "error": "Could not identify Frame.io Team ID."}
                        
                    url = f"{base_url}/teams/{team_id}/projects"
                    async with session.get(url, headers=headers) as resp:
                        res_data = await resp.json()
                        return {"status": "success", "data": {"result": res_data}}

                elif action == "list_assets":
                    p_id = self.get_config("project_id") or str(input_data)
                    url = f"{base_url}/projects/{p_id}/assets"
                    async with session.get(url, headers=headers) as resp:
                        res_data = await resp.json()
                        return {"status": "success", "data": {"result": res_data}}

                return {"status": "error", "error": f"Unsupported action: {action}"}

        except Exception as e:
            return {"status": "error", "error": f"Frame.io Node Failed: {str(e)}"}