"""
Pinterest Node - Studio Standard (Universal Method)
Batch 106: Social Media
"""
from typing import Any, Dict, Optional
import aiohttp
from ..base import BaseNode
from ..registry import register_node

@register_node("pinterest_node")
class PinterestNode(BaseNode):
    """
    Pinterest integration for creating pins and boards.
    """
    node_type = "pinterest_node"
    version = "1.0.0"
    category = "social_media"
    credentials_required = ["pinterest_auth"]


    properties = [
        {
            'displayName': 'Operation',
            'name': 'operation',
            'type': 'options',
            'default': 'create_pin',
            'options': [
                {'name': 'Create Pin', 'value': 'create_pin'},
                {'name': 'Create Board', 'value': 'create_board'},
                {'name': 'List Boards', 'value': 'list_boards'},
            ],
            'description': 'Pinterest action',
        },
        {
            'displayName': 'Board Id',
            'name': 'board_id',
            'type': 'string',
            'default': '',
        },
        {
            'displayName': 'Description',
            'name': 'description',
            'type': 'string',
            'default': '',
        },
        {
            'displayName': 'Image Url',
            'name': 'image_url',
            'type': 'string',
            'default': '',
        },
        {
            'displayName': 'Title',
            'name': 'title',
            'type': 'string',
            'default': '',
        },
    ]
    inputs = {
        "action": {
            "type": "dropdown",
            "default": "create_pin",
            "options": ["create_pin", "create_board", "list_boards"],
            "description": "Pinterest action"
        },
        "board_id": {
            "type": "string",
            "optional": True
        },
        "image_url": {
            "type": "string",
            "optional": True
        },
        "title": {
            "type": "string",
            "optional": True
        },
        "description": {
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
            creds = await self.get_credential("pinterest_auth")
            access_token = creds.get("access_token")
            
            if not access_token:
                return {"status": "error", "error": "Pinterest access token required"}

            base_url = "https://api.pinterest.com/v5"
            headers = {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json"
            }
            
            action = self.get_config("action", "create_pin")

            async with aiohttp.ClientSession() as session:
                if action == "create_pin":
                    board_id = self.get_config("board_id")
                    image_url = self.get_config("image_url")
                    title = self.get_config("title")
                    
                    if not board_id or not image_url:
                        return {"status": "error", "error": "board_id and image_url required"}
                    
                    payload = {
                        "board_id": board_id,
                        "media_source": {
                            "source_type": "image_url",
                            "url": image_url
                        },
                        "title": title
                    }
                    description = self.get_config("description")
                    if description:
                         payload["description"] = description
                         
                    url = f"{base_url}/pins"
                    async with session.post(url, headers=headers, json=payload) as resp:
                        if resp.status != 201:
                            error_text = await resp.text()
                            return {"status": "error", "error": f"Pinterest API Error {resp.status}: {error_text}"}
                        res_data = await resp.json()
                        return {"status": "success", "data": {"result": res_data}}
                
                elif action == "list_boards":
                    url = f"{base_url}/boards"
                    async with session.get(url, headers=headers) as resp:
                        if resp.status != 200:
                            error_text = await resp.text()
                            return {"status": "error", "error": f"Pinterest API Error {resp.status}: {error_text}"}
                        res_data = await resp.json()
                        return {"status": "success", "data": {"result": res_data.get("items", [])}}

            return {"status": "error", "error": f"Unsupported action: {action}"}

        except Exception as e:
            return {"status": "error", "error": f"Pinterest Node Failed: {str(e)}"}