"""
Confluence Node - Studio Standard
Batch 60: Knowledge Management
"""
from typing import Any, Dict, Optional, List
import aiohttp
import base64
import json
from ..base import BaseNode
from ..registry import register_node

@register_node("confluence_node")
class ConfluenceNode(BaseNode):
    """
    Enterprise-grade Confluence interaction for shared documentation.
    Supports creating, fetching, and searching wiki pages.
    """
    node_type = "confluence_node"
    version = "1.1.0"
    category = "knowledge"
    credentials_required = ["confluence_auth"]


    properties = [
        {
            'displayName': 'Operation',
            'name': 'operation',
            'type': 'options',
            'default': 'get_page',
            'options': [
                {'name': 'Get Page', 'value': 'get_page'},
                {'name': 'Create Page', 'value': 'create_page'},
                {'name': 'List Spaces', 'value': 'list_spaces'},
                {'name': 'Search Content', 'value': 'search_content'},
                {'name': 'Add Comment', 'value': 'add_comment'},
            ],
            'description': 'Confluence action',
        },
        {
            'displayName': 'Content',
            'name': 'content',
            'type': 'string',
            'default': '',
            'description': 'Page body (XHTML/Storage format)',
        },
        {
            'displayName': 'Domain',
            'name': 'domain',
            'type': 'string',
            'default': '',
            'description': 'Atlassian Cloud Domain (e.g. company.atlassian.net)',
            'required': True,
        },
        {
            'displayName': 'Page Id',
            'name': 'page_id',
            'type': 'string',
            'default': '',
            'description': 'ID of the specific page',
        },
        {
            'displayName': 'Space Key',
            'name': 'space_key',
            'type': 'string',
            'default': '',
            'description': 'Space key (e.g. 'DEV')',
        },
        {
            'displayName': 'Title',
            'name': 'title',
            'type': 'string',
            'default': '',
            'description': 'Page or comment title',
        },
    ]
    inputs = {
        "action": {
            "type": "dropdown",
            "default": "get_page",
            "options": ["get_page", "create_page", "list_spaces", "search_content", "add_comment"],
            "description": "Confluence action"
        },
        "domain": {
            "type": "string",
            "required": True,
            "description": "Atlassian Cloud Domain (e.g. company.atlassian.net)"
        },
        "page_id": {
            "type": "string",
            "optional": True,
            "description": "ID of the specific page"
        },
        "space_key": {
            "type": "string",
            "optional": True,
            "description": "Space key (e.g. 'DEV')"
        },
        "title": {
            "type": "string",
            "optional": True,
            "description": "Page or comment title"
        },
        "content": {
            "type": "string",
            "optional": True,
            "description": "Page body (XHTML/Storage format)"
        }
    }

    outputs = {
        "result": {"type": "any"},
        "status": {"type": "string"},
        "url": {"type": "string"}
    }

    async def execute(self, input_data: Any, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        try:
            # 1. Resolve Auth
            creds = await self.get_credential("confluence_auth")
            email = creds.get("email") if creds else self.get_config("email")
            api_token = creds.get("api_token") if creds else self.get_config("api_token")
            domain = self.get_config("domain").rstrip("/")
            
            if not all([email, api_token, domain]):
                return {"status": "error", "error": "Confluence Email, API Token, and Domain are required."}

            # Atlassian Basic Auth: email:api_token
            auth_str = f"{email}:{api_token}"
            encoded_auth = base64.b64encode(auth_str.encode()).decode()
            
            headers = {
                "Authorization": f"Basic {encoded_auth}",
                "Accept": "application/json",
                "Content-Type": "application/json"
            }
            
            base_url = f"https://{domain}/wiki/rest/api"
            action = self.get_config("action", "get_page")

            async with aiohttp.ClientSession() as session:
                if action == "get_page":
                    page_id = self.get_config("page_id") or str(input_data)
                    url = f"{base_url}/content/{page_id}?expand=body.storage"
                    async with session.get(url, headers=headers) as resp:
                        res_data = await resp.json()
                        return {
                            "status": "success",
                            "data": {
                                "result": res_data,
                                "url": f"https://{domain}/wiki{res_data.get('_links', {}).get('webui')}"
                            }
                        }

                elif action == "create_page":
                    url = f"{base_url}/content"
                    space_key = self.get_config("space_key")
                    title = self.get_config("title") or "New Page from Studio"
                    content = self.get_config("content") or str(input_data)
                    
                    payload = {
                        "type": "page",
                        "title": title,
                        "space": {"key": space_key},
                        "body": {
                            "storage": {
                                "value": content,
                                "representation": "storage"
                            }
                        }
                    }
                    async with session.post(url, headers=headers, json=payload) as resp:
                        res_data = await resp.json()
                        return {
                            "status": "success",
                            "data": {
                                "result": res_data,
                                "url": f"https://{domain}/wiki{res_data.get('_links', {}).get('webui')}",
                                "status": "created"
                            }
                        }

                elif action == "list_spaces":
                    url = f"{base_url}/space"
                    async with session.get(url, headers=headers) as resp:
                        res_data = await resp.json()
                        return {"status": "success", "data": {"result": res_data.get("results"), "count": res_data.get("size")}}

                elif action == "search_content":
                    query = self.get_config("title") or str(input_data)
                    url = f"{base_url}/content/search"
                    params = {"cql": f"text ~ '{query}'"}
                    async with session.get(url, headers=headers, params=params) as resp:
                        res_data = await resp.json()
                        return {"status": "success", "data": {"result": res_data.get("results"), "count": res_data.get("size")}}

                return {"status": "error", "error": f"Unsupported Confluence action: {action}"}

        except Exception as e:
            return {"status": "error", "error": f"Confluence Node Failed: {str(e)}"}