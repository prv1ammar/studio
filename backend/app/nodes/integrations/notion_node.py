from typing import Any, Dict, Optional, List
from ..base import BaseNode
from ..registry import register_node
from notion_client import Client

@register_node("notion_action")
class NotionNode(BaseNode):
    """
    Integrates with Notion for database reading and page creation.
    """
    node_type = "notion_action"
    version = "1.0.0"
    category = "integrations"
    credentials_required = ["notion_auth"]

    inputs = {
        "action": {"type": "string", "default": "create_page", "enum": ["create_page", "query_database"]},
        "database_id": {"type": "string", "optional": True},
        "page_id": {"type": "string", "optional": True, "description": "Parent page ID for sub-pages"}
    }
    outputs = {
        "id": {"type": "string"},
        "results": {"type": "array"},
        "status": {"type": "string"}
    }

    async def execute(self, input_data: Any, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        try:
            # 1. Resolve Auth
            creds = await self.get_credential("notion_auth")
            token = creds.get("token") or creds.get("api_key") if creds else self.get_config("api_key")
            
            if not token:
                return {"status": "error", "error": "Notion Token is required."}

            notion = Client(auth=token)
            action = self.get_config("action", "create_page")
            
            if action == "query_database":
                db_id = self.get_config("database_id")
                if not db_id:
                    return {"status": "error", "error": "Database ID is required for Query action."}
                results = notion.databases.query(database_id=db_id)
                return {
                    "status": "success",
                    "data": {
                        "results": results.get("results", []),
                        "count": len(results.get("results", []))
                    }
                }

            elif action == "create_page":
                db_id = self.get_config("database_id")
                parent_page_id = self.get_config("page_id")
                
                title = "New Page from Studio"
                if isinstance(input_data, str):
                    title = input_data
                elif isinstance(input_data, dict):
                    title = input_data.get("title") or input_data.get("name") or title

                if db_id:
                    new_page = notion.pages.create(
                        parent={"database_id": db_id},
                        properties={"Name": {"title": [{"text": {"content": title}}]}}
                    )
                elif parent_page_id:
                    new_page = notion.pages.create(
                        parent={"page_id": parent_page_id},
                        properties={"title": [{"text": {"content": title}}]}
                    )
                else:
                    return {"status": "error", "error": "Either Database ID or Parent Page ID must be provided."}

                return {
                    "status": "success",
                    "data": {
                        "id": new_page["id"],
                        "url": new_page.get("url")
                    }
                }

            return {"status": "error", "error": f"Unsupported action: {action}"}

        except Exception as e:
            return {"status": "error", "error": f"Notion Node Error: {str(e)}"}
