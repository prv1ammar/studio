"""
Cohere Rerank Node - Studio Standard (Universal Method)
Batch 118: AI Essentials & Local Inference
"""
from typing import Any, Dict, Optional, List
import aiohttp
from ..base import BaseNode
from ..registry import register_node

@register_node("cohere_rerank_node")
class CohereRerankNode(BaseNode):
    """
    Rerank documents using Cohere's advanced reranking models for better RAG precision.
    """
    node_type = "cohere_rerank_node"
    version = "1.0.0"
    category = "processing"
    credentials_required = ["cohere_auth"]


    properties = [
        {
            'displayName': 'Documents',
            'name': 'documents',
            'type': 'string',
            'default': '',
            'description': 'List of strings or objects to rerank',
            'required': True,
        },
        {
            'displayName': 'Model',
            'name': 'model',
            'type': 'options',
            'default': 'rerank-english-v3.0',
            'options': [
                {'name': 'Rerank-English-V3.0', 'value': 'rerank-english-v3.0'},
                {'name': 'Rerank-Multilingual-V3.0', 'value': 'rerank-multilingual-v3.0'},
                {'name': 'Rerank-English-V2.0', 'value': 'rerank-english-v2.0'},
                {'name': 'Rerank-Multilingual-V2.0', 'value': 'rerank-multilingual-v2.0'},
            ],
        },
        {
            'displayName': 'Query',
            'name': 'query',
            'type': 'string',
            'default': '',
            'description': 'The search query used to find the documents',
            'required': True,
        },
        {
            'displayName': 'Top N',
            'name': 'top_n',
            'type': 'string',
            'default': 3,
            'description': 'Number of top results to return',
        },
    ]
    inputs = {
        "query": {
            "type": "string",
            "required": True,
            "description": "The search query used to find the documents"
        },
        "documents": {
            "type": "list",
            "required": True,
            "description": "List of strings or objects to rerank"
        },
        "model": {
            "type": "dropdown",
            "default": "rerank-english-v3.0",
            "options": [
                "rerank-english-v3.0",
                "rerank-multilingual-v3.0",
                "rerank-english-v2.0",
                "rerank-multilingual-v2.0"
            ]
        },
        "top_n": {
            "type": "number",
            "default": 3,
            "description": "Number of top results to return"
        }
    }

    outputs = {
        "results": {"type": "list"},
        "status": {"type": "string"}
    }

    async def execute(self, input_data: Any, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        try:
            creds = await self.get_credential("cohere_auth")
            api_key = creds.get("api_key")
            
            if not api_key:
                return {"status": "error", "error": "Cohere API Key is required"}

            query = self.get_config("query") or str(input_data)
            docs = self.get_config("documents") or []
            if not docs and isinstance(input_data, list):
                docs = input_data

            if not docs:
                return {"status": "success", "data": {"results": []}}

            # Normalize documents to strings for the API
            doc_strings = []
            for d in docs:
                if isinstance(d, str):
                    doc_strings.append(d)
                elif isinstance(d, dict):
                    # Try common content fields
                    doc_strings.append(d.get("text", d.get("content", str(d))))
                else:
                    doc_strings.append(str(d))

            url = "https://api.cohere.ai/v1/rerank"
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            }
            payload = {
                "model": self.get_config("model", "rerank-english-v3.0"),
                "query": query,
                "documents": doc_strings,
                "top_n": int(self.get_config("top_n", 3))
            }

            async with aiohttp.ClientSession() as session:
                async with session.post(url, headers=headers, json=payload) as response:
                    if response.status != 200:
                        text = await response.text()
                        return {"status": "error", "error": f"Cohere error {response.status}: {text}"}
                    
                    data = await response.json()

            # Map results back to original documents for better preservation of metadata if any
            reranked_results = []
            for res in data.get("results", []):
                idx = res["index"]
                reranked_results.append({
                    "document": docs[idx],
                    "relevance_score": res["relevance_score"]
                })

            return {
                "status": "success",
                "data": {
                    "results": reranked_results
                }
            }

        except Exception as e:
            return {"status": "error", "error": f"Cohere Rerank failed: {str(e)}"}