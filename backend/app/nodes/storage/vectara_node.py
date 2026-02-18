"""
Vectara Node - Studio Standard (Universal Method)
Batch 115: Specialized Tools
"""
from typing import Any, Dict, Optional, List
import aiohttp
from ..base import BaseNode
from ..registry import register_node

@register_node("vectara_node")
class VectaraNode(BaseNode):
    """
    Search and store data in Vectara (Agnostic Semantic Search).
    """
    node_type = "vectara_node"
    version = "1.0.0"
    category = "storage"
    credentials_required = ["vectara_auth"]


    properties = [
        {
            'displayName': 'Operation',
            'name': 'operation',
            'type': 'options',
            'default': 'search',
            'options': [
                {'name': 'Search', 'value': 'search'},
                {'name': 'Index Document', 'value': 'index_document'},
            ],
            'description': 'Vectara action to perform',
        },
        {
            'displayName': 'Corpus Id',
            'name': 'corpus_id',
            'type': 'string',
            'default': '',
            'description': 'The ID of the Vectara corpus',
            'required': True,
        },
        {
            'displayName': 'Query',
            'name': 'query',
            'type': 'string',
            'default': '',
            'description': 'Enter your search query or document text',
        },
        {
            'displayName': 'Top K',
            'name': 'top_k',
            'type': 'string',
            'default': 10,
        },
    ]
    inputs = {
        "action": {
            "type": "dropdown",
            "default": "search",
            "options": ["search", "index_document"],
            "description": "Vectara action to perform"
        },
        "query": {
            "type": "string",
            "optional": True,
            "description": "Enter your search query or document text"
        },
        "corpus_id": {
            "type": "string",
            "required": True,
            "description": "The ID of the Vectara corpus"
        },
        "top_k": {
            "type": "number",
            "default": 10
        }
    }

    outputs = {
        "results": {"type": "list"},
        "status": {"type": "string"}
    }

    async def execute(self, input_data: Any, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        try:
            creds = await self.get_credential("vectara_auth")
            customer_id = creds.get("customer_id")
            api_key = creds.get("api_key")
            
            if not customer_id or not api_key:
                return {"status": "error", "error": "Vectara Customer ID and API Key are required"}

            action = self.get_config("action", "search")
            corpus_id = self.get_config("corpus_id")
            query = self.get_config("query") or str(input_data)
            top_k = int(self.get_config("top_k", 10))

            base_url = "https://api.vectara.io/v1"
            headers = {
                "x-api-key": api_key,
                "customer-id": customer_id,
                "Content-Type": "application/json"
            }

            async with aiohttp.ClientSession() as session:
                if action == "search":
                    payload = {
                        "query": [{
                            "query": query,
                            "num_results": top_k,
                            "corpus_key": [{"corpus_id": corpus_id}]
                        }]
                    }
                    async with session.post(f"{base_url}/query", headers=headers, json=payload) as response:
                        data = await response.json()
                        # Extract results from Vectara response structure
                        results = data.get("responseSet", [{}])[0].get("response", [])
                        return {"status": "success", "data": {"results": results}}

                elif action == "index_document":
                    payload = {
                        "customer_id": int(customer_id),
                        "corpus_id": int(corpus_id),
                        "document": {
                            "document_id": f"doc_{hash(query)}",
                            "title": "Indexed from Studio",
                            "section": [{"text": query}]
                        }
                    }
                    async with session.post(f"{base_url}/index", headers=headers, json=payload) as response:
                        data = await response.json()
                        return {"status": "success", "data": {"results": data}}

            return {"status": "error", "error": f"Unsupported action: {action}"}

        except Exception as e:
            return {"status": "error", "error": f"Vectara failure: {str(e)}"}