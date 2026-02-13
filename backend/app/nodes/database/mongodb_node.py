"""
MongoDB Node - Studio Standard (Universal Method)
Batch 95: Database Connectors (n8n Critical - Enhanced)
"""
from typing import Any, Dict, Optional, List
import motor.motor_asyncio
from ...base import BaseNode
from ...registry import register_node

@register_node("mongodb_node")
class MongoDBNode(BaseNode):
    """
    Execute CRUD operations on MongoDB.
    """
    node_type = "mongodb_node"
    version = "1.0.0"
    category = "database"
    credentials_required = ["mongodb_auth"]

    inputs = {
        "action": {
            "type": "dropdown",
            "default": "find_items",
            "options": ["find_items", "insert_item", "update_item", "delete_item", "aggregate"],
            "description": "MongoDB action"
        },
        "collection": {
            "type": "string",
            "required": True
        },
        "query": {
            "type": "string",
            "optional": True,
            "description": "Query JSON"
        },
        "document": {
            "type": "string",
            "optional": True,
            "description": "Document JSON for insert/update"
        }
    }

    outputs = {
        "result": {"type": "any"},
        "status": {"type": "string"}
    }

    async def execute(self, input_data: Any, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        try:
            # 1. Authentication
            creds = await self.get_credential("mongodb_auth")
            uri = creds.get("connection_string") or f"mongodb://{creds.get('host', 'localhost')}:{creds.get('port', 27017)}"
            db_name = creds.get("database")
            
            if not uri:
                return {"status": "error", "error": "MongoDB Connection String required."}

            client = motor.motor_asyncio.AsyncIOMotorClient(uri)
            db = client[db_name]
            
            action = self.get_config("action", "find_items")
            collection_name = self.get_config("collection")
            if not collection_name:
                return {"status": "error", "error": "collection required"}

            collection = db[collection_name]
            
            import json
            query_str = self.get_config("query", "{}")
            query = json.loads(query_str) if isinstance(query_str, str) else query_str
            
            if action == "find_items":
                cursor = collection.find(query)
                results = await cursor.to_list(length=100)
                # Convert ObjectId to str
                for doc in results:
                    if "_id" in doc: doc["_id"] = str(doc["_id"])
                return {"status": "success", "data": {"result": results}}

            elif action == "insert_item":
                doc_str = self.get_config("document") or str(input_data)
                document = json.loads(doc_str) if isinstance(doc_str, str) else doc_str
                
                result = await collection.insert_one(document)
                return {"status": "success", "data": {"result": {"inserted_id": str(result.inserted_id)}}}

            elif action == "update_item":
                update_str = self.get_config("document")
                update = json.loads(update_str) if isinstance(update_str, str) else update_str
                
                result = await collection.update_many(query, {"$set": update})
                return {"status": "success", "data": {"result": {"modified_count": result.modified_count}}}

            elif action == "delete_item":
                result = await collection.delete_many(query)
                return {"status": "success", "data": {"result": {"deleted_count": result.deleted_count}}}

            return {"status": "error", "error": f"Unsupported action: {action}"}

        except Exception as e:
            return {"status": "error", "error": f"MongoDB Node Failed: {str(e)}"}
