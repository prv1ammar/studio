"""
Wistia Node - Studio Standard
Batch 79: Media Production
"""
from typing import Any, Dict, Optional, List
import aiohttp
from ..base import BaseNode
from ..registry import register_node

@register_node("wistia_node")
class WistiaNode(BaseNode):
    """
    Access video analytics and project management via the Wistia Data API.
    """
    node_type = "wistia_node"
    version = "1.0.0"
    category = "media"
    credentials_required = ["wistia_auth"]


    properties = [
        {
            'displayName': 'Operation',
            'name': 'operation',
            'type': 'options',
            'default': 'list_projects',
            'options': [
                {'name': 'List Projects', 'value': 'list_projects'},
                {'name': 'List Medias', 'value': 'list_medias'},
                {'name': 'Get Media Stats', 'value': 'get_media_stats'},
                {'name': 'Get Media Details', 'value': 'get_media_details'},
            ],
            'description': 'Wistia action',
        },
        {
            'displayName': 'Media Id',
            'name': 'media_id',
            'type': 'string',
            'default': '',
            'description': 'Unique hashed ID for the media',
        },
        {
            'displayName': 'Project Id',
            'name': 'project_id',
            'type': 'string',
            'default': '',
            'description': 'Unique hashed ID for the project',
        },
    ]
    inputs = {
        "action": {
            "type": "dropdown",
            "default": "list_projects",
            "options": ["list_projects", "list_medias", "get_media_stats", "get_media_details"],
            "description": "Wistia action"
        },
        "project_id": {
            "type": "string",
            "optional": True,
            "description": "Unique hashed ID for the project"
        },
        "media_id": {
            "type": "string",
            "optional": True,
            "description": "Unique hashed ID for the media"
        }
    }

    outputs = {
        "result": {"type": "any"},
        "status": {"type": "string"},
        "count": {"type": "number"}
    }

    async def execute(self, input_data: Any, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        try:
            creds = await self.get_credential("wistia_auth")
            api_token = creds.get("api_token") if creds else self.get_config("api_token")
            
            if not api_token:
                return {"status": "error", "error": "Wistia API Token is required."}

            headers = {
                "Authorization": f"Bearer {api_token}",
                "Accept": "application/json"
            }
            
            base_url = "https://api.wistia.com/v1"
            action = self.get_config("action", "list_projects")

            async with aiohttp.ClientSession() as session:
                if action == "list_projects":
                    url = f"{base_url}/projects.json"
                    async with session.get(url, headers=headers) as resp:
                        res_data = await resp.json()
                        return {"status": "success", "data": {"result": res_data, "count": len(res_data)}}

                elif action == "list_medias":
                    p_id = self.get_config("project_id")
                    url = f"{base_url}/medias.json"
                    params = {"project_id": p_id} if p_id else {}
                    async with session.get(url, headers=headers, params=params) as resp:
                        res_data = await resp.json()
                        return {"status": "success", "data": {"result": res_data, "count": len(res_data)}}

                elif action == "get_media_stats":
                    m_id = self.get_config("media_id") or str(input_data)
                    url = f"{base_url}/stats/medias/{m_id}.json"
                    async with session.get(url, headers=headers) as resp:
                        res_data = await resp.json()
                        return {"status": "success", "data": {"result": res_data}}

                return {"status": "error", "error": f"Unsupported action: {action}"}

        except Exception as e:
            return {"status": "error", "error": f"Wistia Node Failed: {str(e)}"}