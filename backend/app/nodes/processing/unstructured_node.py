"""
Unstructured Node - Studio Standard (Universal Method)
Batch 117: Advanced Document Processing
"""
from typing import Any, Dict, Optional, List
import aiohttp
from ..base import BaseNode
from ..registry import register_node

@register_node("unstructured_node")
class UnstructuredNode(BaseNode):
    """
    Extract clean text from documents using Unstructured.io.
    """
    node_type = "unstructured_node"
    version = "1.0.0"
    category = "processing"
    credentials_required = ["unstructured_auth"]


    properties = [
        {
            'displayName': 'Api Url',
            'name': 'api_url',
            'type': 'string',
            'default': 'https://api.unstructured.io/general/v0/general',
        },
        {
            'displayName': 'Chunking Strategy',
            'name': 'chunking_strategy',
            'type': 'options',
            'default': 'by_title',
            'options': [
                {'name': 'Basic', 'value': 'basic'},
                {'name': 'By Title', 'value': 'by_title'},
                {'name': 'By Page', 'value': 'by_page'},
                {'name': 'By Similarity', 'value': 'by_similarity'},
            ],
            'description': 'Strategy for breaking down documents',
        },
        {
            'displayName': 'File Path',
            'name': 'file_path',
            'type': 'string',
            'default': '',
            'description': 'Local path or URL to the document',
            'required': True,
        },
    ]
    inputs = {
        "file_path": {
            "type": "string",
            "required": True,
            "description": "Local path or URL to the document"
        },
        "chunking_strategy": {
            "type": "dropdown",
            "default": "by_title",
            "options": ["basic", "by_title", "by_page", "by_similarity"],
            "description": "Strategy for breaking down documents"
        },
        "api_url": {
            "type": "string",
            "default": "https://api.unstructured.io/general/v0/general"
        }
    }

    outputs = {
        "text": {"type": "string"},
        "elements": {"type": "list"},
        "status": {"type": "string"}
    }

    async def execute(self, input_data: Any, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        try:
            creds = await self.get_credential("unstructured_auth")
            api_key = creds.get("api_key")
            
            if not api_key:
                return {"status": "error", "error": "Unstructured API Key is required"}

            file_path = self.get_config("file_path") or str(input_data)
            strategy = self.get_config("chunking_strategy", "by_title")
            url = self.get_config("api_url", "https://api.unstructured.io/general/v0/general")

            headers = {
                "unstructured-api-key": api_key,
                "Accept": "application/json"
            }
            
            # Note: Unstructured API usually requires multipart/form-data for file uploads.
            # For this node, we'll assume we're sending a URL or local path that the API can handle
            # or we might need to physically upload. For simplicity in this base version,
            # we'll handle URL-based partition if provided, otherwise error.
            
            if not file_path.startswith("http"):
                return {"status": "error", "error": f"Local file upload not yet implemented in node. Please provide a URL."}

            payload = {
                "url": file_path,
                "chunking_strategy": strategy
            }

            async with aiohttp.ClientSession() as session:
                async with session.post(url, headers=headers, json=payload) as response:
                    if response.status != 200:
                        text = await response.text()
                        return {"status": "error", "error": f"Unstructured Error {response.status}: {text}"}
                    
                    data = await response.json()

            combined_text = "\n\n".join([el.get("text", "") for el in data if "text" in el])
            return {
                "status": "success",
                "data": {
                    "text": combined_text,
                    "elements": data
                }
            }

        except Exception as e:
            return {"status": "error", "error": f"Unstructured failed: {str(e)}"}