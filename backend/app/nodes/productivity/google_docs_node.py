"""
Google Docs Node - Studio Standard (Universal Method)
Batch 91: Productivity Suite (n8n Critical)
"""
from typing import Any, Dict, Optional, List
import aiohttp
from ...base import BaseNode
from ...registry import register_node

@register_node("google_docs_node")
class GoogleDocsNode(BaseNode):
    """
    Create and manage Google Docs documents via Google Docs API.
    """
    node_type = "google_docs_node"
    version = "1.0.0"
    category = "productivity"
    credentials_required = ["google_auth"]

    inputs = {
        "action": {
            "type": "dropdown",
            "default": "create_document",
            "options": ["create_document", "get_document", "append_text", "replace_text"],
            "description": "Google Docs action"
        },
        "document_id": {
            "type": "string",
            "optional": True
        },
        "title": {
            "type": "string",
            "optional": True
        },
        "text": {
            "type": "string",
            "optional": True
        }
    }

    outputs = {
        "result": {"type": "any"},
        "status": {"type": "string"},
        "document_url": {"type": "string", "optional": True}
    }

    async def execute(self, input_data: Any, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        try:
            # 1. Authentication
            creds = await self.get_credential("google_auth")
            access_token = creds.get("access_token")
            
            if not access_token:
                return {"status": "error", "error": "Google Access Token required."}

            headers = {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json"
            }
            
            # 2. Connect to Real API
            docs_url = "https://docs.googleapis.com/v1/documents"
            action = self.get_config("action", "create_document")

            async with aiohttp.ClientSession() as session:
                if action == "create_document":
                    title = self.get_config("title", "Studio Document")
                    
                    payload = {
                        "title": title
                    }
                    async with session.post(docs_url, headers=headers, json=payload) as resp:
                        if resp.status not in [200, 201]:
                            return {"status": "error", "error": f"Google Docs Error: {resp.status}"}
                        res_data = await resp.json()
                        doc_id = res_data.get("documentId")
                        return {
                            "status": "success",
                            "data": {
                                "result": res_data,
                                "document_url": f"https://docs.google.com/document/d/{doc_id}/edit"
                            }
                        }

                elif action == "get_document":
                    doc_id = self.get_config("document_id") or str(input_data)
                    url = f"{docs_url}/{doc_id}"
                    async with session.get(url, headers=headers) as resp:
                        if resp.status != 200:
                            return {"status": "error", "error": f"Google Docs Error: {resp.status}"}
                        res_data = await resp.json()
                        return {"status": "success", "data": {"result": res_data}}

                elif action == "append_text":
                    doc_id = self.get_config("document_id")
                    text = self.get_config("text") or str(input_data)
                    
                    if not doc_id:
                        return {"status": "error", "error": "document_id required"}
                    
                    url = f"{docs_url}/{doc_id}:batchUpdate"
                    payload = {
                        "requests": [{
                            "insertText": {
                                "location": {"index": 1},
                                "text": text
                            }
                        }]
                    }
                    async with session.post(url, headers=headers, json=payload) as resp:
                        if resp.status != 200:
                            return {"status": "error", "error": f"Google Docs Error: {resp.status}"}
                        res_data = await resp.json()
                        return {"status": "success", "data": {"result": res_data}}

                return {"status": "error", "error": f"Unsupported action: {action}"}

        except Exception as e:
            return {"status": "error", "error": f"Google Docs Node Failed: {str(e)}"}
