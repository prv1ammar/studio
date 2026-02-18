"""
Sanity Node - Studio Standard
Batch 71: CMS & Web Engines
"""
from typing import Any, Dict, Optional, List
import aiohttp
from ..base import BaseNode
from ..registry import register_node

@register_node("sanity_node")
class SanityNode(BaseNode):
    """
    Headless content lake orchestration via Sanity.io.
    """
    node_type = "sanity_node"
    version = "1.0.0"
    category = "cms"
    credentials_required = ["sanity_auth"]


    properties = [
        {
            'displayName': 'Operation',
            'name': 'operation',
            'type': 'options',
            'default': 'query',
            'options': [
                {'name': 'Query', 'value': 'query'},
                {'name': 'Get Document', 'value': 'get_document'},
                {'name': 'Create Document', 'value': 'create_document'},
            ],
            'description': 'Sanity action',
        },
        {
            'displayName': 'Api Version',
            'name': 'api_version',
            'type': 'string',
            'default': '2023-01-01',
        },
        {
            'displayName': 'Dataset',
            'name': 'dataset',
            'type': 'string',
            'default': 'production',
        },
        {
            'displayName': 'Document Type',
            'name': 'document_type',
            'type': 'string',
            'default': '',
            'description': 'Document type for creation',
        },
        {
            'displayName': 'Project Id',
            'name': 'project_id',
            'type': 'string',
            'default': '',
            'required': True,
        },
        {
            'displayName': 'Query',
            'name': 'query',
            'type': 'string',
            'default': '',
            'description': 'GROQ query string',
        },
    ]
    inputs = {
        "action": {
            "type": "dropdown",
            "default": "query",
            "options": ["query", "get_document", "create_document"],
            "description": "Sanity action"
        },
        "project_id": {
            "type": "string",
            "required": True
        },
        "dataset": {
            "type": "string",
            "default": "production"
        },
        "api_version": {
            "type": "string",
            "default": "2023-01-01"
        },
        "query": {
            "type": "string",
            "optional": True,
            "description": "GROQ query string"
        },
        "document_type": {
            "type": "string",
            "optional": True,
            "description": "Document type for creation"
        }
    }

    outputs = {
        "result": {"type": "any"},
        "status": {"type": "string"},
        "count": {"type": "number"}
    }

    async def execute(self, input_data: Any, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        try:
            creds = await self.get_credential("sanity_auth")
            token = creds.get("token") if creds else self.get_config("token")
            
            if not token:
                return {"status": "error", "error": "Sanity Token is required."}

            headers = {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json"
            }
            
            p_id = self.get_config("project_id")
            dataset = self.get_config("dataset", "production")
            v = self.get_config("api_version", "2023-01-01")
            
            base_url = f"https://{p_id}.api.sanity.io/v{v}/data"
            action = self.get_config("action", "query")

            async with aiohttp.ClientSession() as session:
                if action == "query":
                    groq_query = self.get_config("query") or str(input_data)
                    url = f"{base_url}/query/{dataset}"
                    params = {"query": groq_query}
                    async with session.get(url, headers=headers, params=params) as resp:
                        res_data = await resp.json()
                        results = res_data.get("result", [])
                        return {"status": "success", "data": {"result": results, "count": len(results)}}

                elif action == "get_document":
                    doc_id = str(input_data)
                    url = f"{base_url}/doc/{dataset}/{doc_id}"
                    async with session.get(url, headers=headers) as resp:
                        res_data = await resp.json()
                        return {"status": "success", "data": {"result": res_data.get("documents", [])}}

                elif action == "create_document":
                    doc_type = self.get_config("document_type")
                    if not doc_type:
                        return {"status": "error", "error": "document_type is required for creation."}
                    
                    doc_data = input_data if isinstance(input_data, dict) else {"content": str(input_data)}
                    payload = {
                        "mutations": [
                            {"create": {**doc_data, "_type": doc_type}}
                        ]
                    }
                    url = f"{base_url}/mutate/{dataset}"
                    async with session.post(url, headers=headers, json=payload) as resp:
                        res_data = await resp.json()
                        return {"status": "success", "data": {"result": res_data, "status": "mutated"}}

                return {"status": "error", "error": f"Unsupported action: {action}"}

        except Exception as e:
            return {"status": "error", "error": f"Sanity Node Failed: {str(e)}"}