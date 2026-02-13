"""
Notion Integration Node - Studio Standard
Batch 40: Productivity Integrations
"""
from typing import Any, Dict, Optional, List
from ...base import BaseNode
from ...registry import register_node

@register_node("notion_node")
class NotionNode(BaseNode):
    """
    Interact with Notion workspaces.
    Supports: Query Database, Create Page, Append Content, Search, Get Page.
    """
    node_type = "notion_node"
    version = "1.0.0"
    category = "productivity"
    credentials_required = ["notion_auth"]

    inputs = {
        "action": {
            "type": "dropdown",
            "default": "query_database",
            "options": ["query_database", "create_page", "append_content", "search", "get_page"],
            "description": "Action to perform"
        },
        "target_id": {
            "type": "string",
            "description": "Database ID or Page ID (depending on action)"
        },
        "content_data": {
            "type": "json",
            "description": "Properties or content blocks (for Create/Append)"
        },
        "query_filter": {
            "type": "json",
            "optional": True,
            "description": "Filter object for Query Database"
        }
    }

    outputs = {
        "results": {"type": "array"},
        "item": {"type": "object"},
        "id": {"type": "string"},
        "url": {"type": "string"}
    }

    async def execute(self, input_data: Any, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        try:
            # Check dependency
            try:
                from notion_client import Client
            except ImportError:
                return {"status": "error", "error": "notion-client not installed. Run: pip install notion-client"}

            # Get Creds
            creds = await self.get_credential("notion_auth")
            token = None
            if creds:
                token = creds.get("token") or creds.get("api_key")
            
            # Fallback to config
            if not token:
                token = self.get_config("api_key")
            
            if not token:
                return {"status": "error", "error": "Notion Integration Token is required."}

            client = Client(auth=token)
            
            # Get Config
            action = self.get_config("action", "query_database")
            target_id = self.get_config("target_id")
            
            # Use input data if provided and appropriate
            content_data = self.get_config("content_data", {})
            if isinstance(input_data, dict):
                 # Merge or override content data
                 content_data.update(input_data)
            elif isinstance(input_data, str) and action in ["create_page", "append_content"]:
                 # If string input, treat as title or paragraph block
                 if action == "create_page":
                     content_data["title"] = input_data
                 else:
                     content_data["text"] = input_data

            result_data = {}

            if action == "query_database":
                if not target_id:
                    return {"status": "error", "error": "Database ID is required for query."}
                
                query_params = {"database_id": target_id}
                filter_obj = self.get_config("query_filter")
                if filter_obj:
                    query_params["filter"] = filter_obj
                    
                response = await client.databases.query(**query_params)
                result_data = {
                    "results": response.get("results", []),
                    "count": len(response.get("results", []))
                }

            elif action == "create_page":
                if not target_id:
                     return {"status": "error", "error": "Database ID (as target_id) is required for create page."}
                
                # Default property structure for a "Name" title property
                title = content_data.get("title", "New Page from Studio")
                properties = content_data.get("properties", {
                    "Name": {"title": [{"text": {"content": title}}]}
                })
                
                response = client.pages.create(
                    parent={"database_id": target_id},
                    properties=properties
                )
                result_data = {
                    "id": response["id"],
                    "url": response["url"],
                    "item": response
                }

            elif action == "append_content":
                if not target_id:
                     return {"status": "error", "error": "Page ID (as target_id) is required to append content."}
                
                # convert simple text to block if needed
                text_content = content_data.get("text")
                children = content_data.get("children", [])
                
                if text_content and not children:
                    children = [{
                        "object": "block",
                        "type": "paragraph",
                        "paragraph": {
                            "rich_text": [{"type": "text", "text": {"content": text_content}}]
                        }
                    }]
                
                if not children:
                     return {"status": "error", "error": "No content (text or children blocks) provided to append."}

                response = client.blocks.children.append(
                    block_id=target_id,
                    children=children
                )
                result_data = {
                    "results": response.get("results", []),
                    "count": len(response.get("results", []))
                }

            elif action == "search":
                query = content_data.get("query", "")
                if isinstance(input_data, str):
                    query = input_data
                
                search_params = {"query": query} if query else {}
                response = await client.search(**search_params)
                result_data = {
                    "results": response.get("results", []),
                    "count": len(response.get("results", []))
                }

            elif action == "get_page":
                if not target_id:
                    return {"status": "error", "error": "Page ID required."}
                response = client.pages.retrieve(page_id=target_id)
                result_data = {"item": response}

            else:
                return {"status": "error", "error": f"Unknown action: {action}"}

            return {
                "status": "success",
                "data": result_data
            }

        except Exception as e:
            return {"status": "error", "error": f"Notion API Failed: {str(e)}"}
