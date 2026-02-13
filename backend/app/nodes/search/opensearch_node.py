"""
OpenSearch Node - Studio Standard
Batch 56: Enterprise Search & Discovery
"""
from typing import Any, Dict, Optional, List
from ...base import BaseNode
from ...registry import register_node
import aiohttp
import json

@register_node("opensearch_node")
class OpenSearchNode(BaseNode):
    """
    Enterprise Search & Analytics via OpenSearch.
    Compatible with Amazon OpenSearch Service and self-hosted clusters.
    """
    node_type = "opensearch_node"
    version = "1.0.0"
    category = "search"
    credentials_required = ["opensearch_auth"]

    inputs = {
        "action": {
            "type": "dropdown",
            "default": "search",
            "options": ["search", "index_document", "delete_document", "create_index"],
            "description": "OpenSearch action"
        },
        "url": {
            "type": "string",
            "required": True,
            "description": "OpenSearch URL (e.g., 'https://your-domain.region.es.amazonaws.com')"
        },
        "index_name": {
            "type": "string",
            "required": True,
            "description": "Index to operate on"
        },
        "query": {
            "type": "string",
            "optional": True,
            "description": "Search query or Query DSL JSON"
        },
        "document": {
            "type": "json",
            "optional": True,
            "description": "Document for indexing"
        },
        "limit": {
            "type": "number",
            "default": 10
        }
    }

    outputs = {
        "results": {"type": "array"},
        "status": {"type": "string"},
        "total": {"type": "number"}
    }

    async def execute(self, input_data: Any, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        try:
            # 1. Resolve Auth
            creds = await self.get_credential("opensearch_auth")
            username = creds.get("username") if creds else self.get_config("username")
            password = creds.get("password") if creds else self.get_config("password")
            
            url = self.get_config("url").rstrip("/")
            index_name = self.get_config("index_name")
            action = self.get_config("action", "search")
            limit = int(self.get_config("limit", 10))

            auth = None
            if username and password:
                auth = aiohttp.BasicAuth(username, password)

            headers = {"Content-Type": "application/json"}
            
            async with aiohttp.ClientSession(auth=auth) as session:
                if action == "search":
                    query_val = self.get_config("query") or (str(input_data) if input_data else "")
                    
                    if query_val.strip().startswith("{"):
                        search_body = json.loads(query_val)
                    else:
                        search_body = {
                            "query": {
                                "multi_match": {
                                    "query": query_val,
                                    "fields": ["*"],
                                    "fuzziness": "AUTO"
                                }
                            },
                            "size": limit
                        }
                    
                    endpoint = f"{url}/{index_name}/_search"
                    async with session.post(endpoint, headers=headers, json=search_body) as resp:
                        res_data = await resp.json()
                        if resp.status >= 400:
                            return {"status": "error", "error": f"OpenSearch Error: {res_data}"}
                        
                        hits = res_data.get("hits", {}).get("hits", [])
                        total = res_data.get("hits", {}).get("total", {}).get("value", 0)
                        
                        return {
                            "status": "success",
                            "data": {
                                "results": [hit["_source"] for hit in hits],
                                "total": total,
                                "status": "searched"
                            }
                        }

                elif action == "index_document":
                    doc = self.get_config("document") or input_data
                    if not isinstance(doc, dict):
                         return {"status": "error", "error": "Document must be a JSON object."}
                    
                    endpoint = f"{url}/{index_name}/_doc"
                    async with session.post(endpoint, headers=headers, json=doc) as resp:
                        res_data = await resp.json()
                        return {
                            "status": "success",
                            "data": {"result": res_data, "status": "indexed"}
                        }

                return {"status": "error", "error": f"Unsupported OpenSearch action: {action}"}

        except Exception as e:
            return {"status": "error", "error": f"OpenSearch Node Failed: {str(e)}"}
