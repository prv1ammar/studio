"""
Elasticsearch Node - Studio Standard (Universal Method)
Batch 113: Intelligent Infrastructure & IoT
"""
from typing import Any, Dict, Optional
import aiohttp
from ...base import BaseNode
from ...registry import register_node

@register_node("elasticsearch_node")
class ElasticsearchNode(BaseNode):
    """
    Interact with Elasticsearch for full-text search and storage.
    """
    node_type = "elasticsearch_node"
    version = "1.0.0"
    category = "database"
    credentials_required = ["elasticsearch_auth"]

    inputs = {
        "action": {
            "type": "dropdown",
            "default": "search",
            "options": ["search", "index_document", "get_document", "delete_document", "list_indices"],
            "description": "Elasticsearch action to perform"
        },
        "index_name": {
            "type": "string",
            "required": True,
            "description": "The index name"
        },
        "query": {
            "type": "string",
            "optional": True,
            "description": "JSON search query or Search string"
        },
        "document": {
            "type": "string",
            "optional": True,
            "description": "JSON document to index"
        },
        "document_id": {
            "type": "string",
            "optional": True
        }
    }

    outputs = {
        "results": {"type": "any"},
        "status": {"type": "string"}
    }

    async def execute(self, input_data: Any, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        try:
            creds = await self.get_credential("elasticsearch_auth")
            url = creds.get("url", "http://localhost:9200").rstrip('/')
            user = creds.get("username")
            password = creds.get("password")
            api_key = creds.get("api_key")
            
            headers = {"Content-Type": "application/json"}
            if api_key:
                headers["Authorization"] = f"ApiKey {api_key}"
            
            auth = None
            if user and password:
                auth = aiohttp.BasicAuth(user, password)

            action = self.get_config("action", "search")
            index = self.get_config("index_name")
            
            async with aiohttp.ClientSession(auth=auth) as session:
                if action == "list_indices":
                    async with session.get(f"{url}/_cat/indices?format=json", headers=headers) as response:
                        data = await response.json()
                        return {"status": "success", "data": {"results": data}}

                elif action == "index_document":
                    doc = self.get_config("document")
                    doc_id = self.get_config("document_id")
                    target_url = f"{url}/{index}/_doc/{doc_id}" if doc_id else f"{url}/{index}/_doc"
                    async with session.post(target_url, headers=headers, data=doc) as response:
                        data = await response.json()
                        return {"status": "success", "data": {"results": data}}

                elif action == "search":
                    query = self.get_config("query")
                    # If query is simple string, wrap in match_all or simple_query_string
                    search_body = query if query and query.startswith('{') else '{"query": {"match_all": {}}}'
                    async with session.post(f"{url}/{index}/_search", headers=headers, data=search_body) as response:
                        data = await response.json()
                        return {"status": "success", "data": {"results": data.get("hits", {}).get("hits", [])}}

            return {"status": "error", "error": f"Unsupported action: {action}"}

        except Exception as e:
            return {"status": "error", "error": f"Elasticsearch Error: {str(e)}"}
