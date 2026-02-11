from typing import Any, Dict, Optional, List
from pydantic import Field
from app.nodes.base import BaseNode, NodeConfig
from notion_client import Client
from app.nodes.registry import register_node

class NotionConfig(NodeConfig):
    database_id: Optional[str] = Field(None, description="The ID of the Notion Database")
    page_id: Optional[str] = Field(None, description="The ID of the Notion Page")
    credentials_id: Optional[str] = Field(None, description="Notion Integration Token Credentials ID")

class NotionDBReaderNode(BaseNode):
    node_id = "notion_db_reader"
    config_model = NotionConfig

    async def execute(self, input_data: Any, context: Optional[Dict[str, Any]] = None) -> Any:
        db_id = self.get_config("database_id")
        creds_data = await self.get_credential("credentials_id")
        token = creds_data.get("token") if creds_data else None

        if not token or not db_id:
            return {"error": "Notion Token and Database ID are required."}

        try:
            notion = Client(auth=token)
            # Fetch results
            results = notion.databases.query(database_id=db_id)
            return results.get("results", [])
        except Exception as e:
            return {"error": f"Notion API Error: {str(e)}"}

class NotionPageCreatorNode(BaseNode):
    node_id = "notion_page_creator"
    config_model = NotionConfig

    async def execute(self, input_data: Any, context: Optional[Dict[str, Any]] = None) -> Any:
        db_id = self.get_config("database_id")
        parent_page_id = self.get_config("page_id")
        creds_data = await self.get_credential("credentials_id")
        token = creds_data.get("token") if creds_data else None

        if not token:
            return {"error": "Notion Token is required."}

        notion = Client(auth=token)

        # Prepare properties based on input_data
        title = "New Page from Studio"
        if isinstance(input_data, str):
            title = input_data
        elif isinstance(input_data, dict):
            title = input_data.get("title", title)

        try:
            if db_id:
                # Add to Database
                new_page = notion.pages.create(
                    parent={"database_id": db_id},
                    properties={
                        "Name": { "title": [ { "text": { "content": title } } ] }
                    }
                )
            elif parent_page_id:
                # Add to Page as sub-page
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

# Register
register_node("notion_db_reader")(NotionDBReaderNode)
register_node("notion_page_creator")(NotionPageCreatorNode)
