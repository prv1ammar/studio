"""
ElasticSearch Node - Studio Standard
Batch 56: Enterprise Search & Discovery
"""
from typing import Any, Dict, Optional, List
from ...base import BaseNode
from ...registry import register_node
import aiohttp
import json

@register_node("elasticsearch_node")
class ElasticSearchNode(BaseNode):
    """
    High-performance Enterprise Search using ElasticSearch.
    Supports indexing, searching, and index management.
    """
    node_type = "elasticsearch_node"
    version = "1.0.0"
    category = "search"
    credentials_required = ["elasticsearch_auth"]

    inputs = {
        "action": {
            "type": "dropdown",
            "default": "search",
            "options": ["search", "index_document", "delete_document", "create_index", "list_indices"],
            "description": "ElasticSearch action to perform"
        },
        "url": {
            "type": "string",
            "required": True,
            "description": "ElasticSearch URL (e.g., 'http://localhost:9200' or Elastic Cloud ID)"
        },
        "index_name": {
            "type": "string",
            "required": True,
            "description": "Index to operate on"
        },
        "query": {
            "type": "string",
            "optional": True,
            "description": "Search query or DSL JSON string"
        },
        "document": {
            "type": "json",
            "optional": True,
            "description": "Document JSON for indexing"
        },
        "document_id": {
            "type": "string",
            "optional": True,
            "description": "Specific document ID"
        },
        "limit": {
            "type": "number",
            "default": 10,
            "description": "Max results to return"
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
            creds = await self.get_credential("elasticsearch_auth")
            api_key = creds.get("api_key") if creds else None
            username = creds.get("username") if creds else self.get_config("username")
            password = creds.get("password") if creds else self.get_config("password")
            
            url = self.get_config("url")
            index_name = self.get_config("index_name")
            action = self.get_config("action", "search")
            limit = int(self.get_config("limit", 10))

            headers = {"Content-Type": "application/json"}
            if api_key:
                headers["Authorization"] = f"ApiKey {api_key}"
            elif username and password:
                import base64
                auth_str = f"{username}:{password}"
                encoded_auth = base64.b64encode(auth_str.encode()).decode()
                headers["Authorization"] = f"Basic {encoded_auth}"

            url = url.rstrip("/")
            
            async with aiohttp.ClientSession() as session:
                if action == "search":
                    query_val = self.get_config("query") or str(input_data)
                    # Check if query is JSON DSL
                    if query_val.strip().startswith("{"):
                        search_body = json.loads(query_val)
                    else:
                        search_body = {
                            "query": {
                                "multi_match": {
                                    "query": query_val,
                                    "fields": ["*"]
                                }
                            },
                            "size": limit
                        }
                    
                    endpoint = f"{url}/{index_name}/_search"
                    async with session.post(endpoint, headers=headers, json=search_body) as resp:
                        res_data = await resp.json()
                        if resp.status >= 400:
                            return {"status": "error", "error": f"Elastic Error: {res_data}"}
                        
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
                    
                    doc_id = self.get_config("document_id")
                    endpoint = f"{url}/{index_name}/_doc"
                    if doc_id:
                        endpoint = f"{endpoint}/{doc_id}"
                    
                    async with session.post(endpoint, headers=headers, json=doc) as resp:
                        res_data = await resp.json()
                        return {
                            "status": "success",
                            "data": {"result": res_data, "status": "indexed"}
                        }

                elif action == "list_indices":
                    endpoint = f"{url}/_cat/indices?format=json"
                    async with session.get(endpoint, headers=headers) as resp:
                        res_data = await resp.json()
                        return {
                            "status": "success",
                            "data": {"results": res_data, "status": "fetched"}
                        }

                return {"status": "error", "error": f"Unsupported action: {action}"}

        except Exception as e:
            return {"status": "error", "error": f"ElasticSearch Node Failed: {str(e)}"}
