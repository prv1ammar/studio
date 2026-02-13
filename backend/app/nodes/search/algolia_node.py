"""
Algolia Search Node - Studio Standard
Batch 56: Enterprise Search & Discovery
"""
from typing import Any, Dict, Optional, List
from ...base import BaseNode
from ...registry import register_node
import aiohttp
import json

@register_node("algolia_node")
class AlgoliaNode(BaseNode):
    """
    Lightning-fast Search and Discovery via Algolia.
    Optimized for e-commerce, documentation, and millisecond-latency search.
    """
    node_type = "algolia_node"
    version = "1.0.0"
    category = "search"
    credentials_required = ["algolia_auth"]

    inputs = {
        "action": {
            "type": "dropdown",
            "default": "search",
            "options": ["search", "add_object", "delete_object", "list_indices"],
            "description": "Algolia action"
        },
        "app_id": {
            "type": "string",
            "required": True,
            "description": "Algolia Application ID"
        },
        "index_name": {
            "type": "string",
            "required": True,
            "description": "Index to operate on"
        },
        "query": {
            "type": "string",
            "optional": True,
            "description": "Search term"
        },
        "object": {
            "type": "json",
            "optional": True,
            "description": "Object to index"
        },
        "hits_per_page": {
            "type": "number",
            "default": 10
        }
    }

    outputs = {
        "results": {"type": "array"},
        "status": {"type": "string"},
        "total_hits": {"type": "number"}
    }

    async def execute(self, input_data: Any, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        try:
            # 1. Resolve Auth
            creds = await self.get_credential("algolia_auth")
            api_key = creds.get("api_key") if creds else self.get_config("api_key")
            app_id = self.get_config("app_id") or (creds.get("app_id") if creds else None)
            
            if not api_key or not app_id:
                return {"status": "error", "error": "Algolia API Key and App ID are required."}

            action = self.get_config("action", "search")
            index_name = self.get_config("index_name")
            query = self.get_config("query") or (str(input_data) if input_data else "")
            
            headers = {
                "X-Algolia-API-Key": api_key,
                "X-Algolia-Application-Id": app_id,
                "Content-Type": "application/json"
            }
            
            # Algolia uses specific host patterns for performance
            read_host = f"https://{app_id}-dsn.algolia.net"
            write_host = f"https://{app_id}.algolia.net"

            async with aiohttp.ClientSession() as session:
                if action == "search":
                    url = f"{read_host}/1/indexes/{index_name}/query"
                    payload = {
                        "params": f"query={query}&hitsPerPage={int(self.get_config('hits_per_page', 10))}"
                    }
                    async with session.post(url, headers=headers, json=payload) as resp:
                        res_data = await resp.json()
                        if resp.status >= 400:
                            return {"status": "error", "error": f"Algolia Error: {res_data}"}
                        
                        hits = res_data.get("hits", [])
                        total = res_data.get("nbHits", 0)
                        
                        return {
                            "status": "success",
                            "data": {
                                "results": hits,
                                "total_hits": total,
                                "status": "searched"
                            }
                        }

                elif action == "add_object":
                    obj = self.get_config("object") or input_data
                    if not isinstance(obj, dict):
                         return {"status": "error", "error": "Object must be a JSON dictionary."}
                    
                    url = f"{write_host}/1/indexes/{index_name}"
                    async with session.post(url, headers=headers, json=obj) as resp:
                        res_data = await resp.json()
                        return {
                            "status": "success",
                            "data": {"result": res_data, "status": "indexed"}
                        }

                elif action == "list_indices":
                    url = f"{read_host}/1/indexes"
                    async with session.get(url, headers=headers) as resp:
                        res_data = await resp.json()
                        return {
                            "status": "success",
                            "data": {"results": res_data.get("items", []), "status": "fetched"}
                        }

                return {"status": "error", "error": f"Unsupported Algolia action: {action}"}

        except Exception as e:
            return {"status": "error", "error": f"Algolia Node Failed: {str(e)}"}
