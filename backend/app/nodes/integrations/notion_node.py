import json
from typing import Any, Dict, Optional, List
from pydantic import Field
from app.nodes.base import BaseNode, NodeConfig
from app.nodes.registry import register_node
from notion_client import Client

class NotionConfig(NodeConfig):
    database_id: Optional[str] = Field(None, description="The ID of the Notion Database")
    page_id: Optional[str] = Field(None, description="The ID of the Notion Page")
    credentials_id: Optional[str] = Field(None, description="Notion Integration Token Credentials ID")

@register_node("notion_db_reader")
class NotionDBReaderNode(BaseNode):
    async def execute(self, input_data: Any, context: Optional[Dict[str, Any]] = None) -> Any:
        db_id = self.get_config("database_id")
        
        creds_data = await self.get_credential("credentials_id")
        token = creds_data.get("token") or creds_data.get("api_key") if creds_data else None

        if not token or not db_id:
            return {"error": "Notion Token and Database ID are required."}

        try:
            notion = Client(auth=token)
            results = notion.databases.query(database_id=db_id)
            return results.get("results", [])
        except Exception as e:
            return {"error": f"Notion API Error: {str(e)}"}

@register_node("notion_page_creator")
class NotionPageCreatorNode(BaseNode):
    async def execute(self, input_data: Any, context: Optional[Dict[str, Any]] = None) -> Any:
        db_id = self.get_config("database_id")
        parent_page_id = self.get_config("page_id")
        
        creds_data = await self.get_credential("credentials_id")
        token = creds_data.get("token") or creds_data.get("api_key") if creds_data else None

        if not token:
            return {"error": "Notion Token is required."}

        notion = Client(auth=token)

        # Title parsing
        title = "New Page from Studio"
        if isinstance(input_data, str):
            title = input_data
        elif isinstance(input_data, dict):
            title = input_data.get("title") or input_data.get("name") or title

        try:
            if db_id:
                # Page in Database
                new_page = notion.pages.create(
                    parent={"database_id": db_id},
                    properties={
                        "Name": { "title": [ { "text": { "content": title } } ] }
                    }
                )
            elif parent_page_id:
                # Sub-page
                new_page = notion.pages.create(
                    parent={"page_id": parent_page_id},
                    properties={
                        "title": [ { "text": { "content": title } } ]
                    }
                )
            else:
                return {"error": "Either Database ID or Parent Page ID must be provided."}

            return {"status": "success", "id": new_page["id"], "url": new_page.get("url")}
        except Exception as e:
            return {"error": f"Notion API Error: {str(e)}"}
