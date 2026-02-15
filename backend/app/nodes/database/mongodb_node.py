"""
MongoDB Node - Studio Standard (Universal Method)
Batch 110: Developer Tools & Databases
"""
from typing import Any, Dict, Optional
import aiohttp
from ...base import BaseNode
from ...registry import register_node

# MongoDB uses `motor` for async access.

@register_node("mongodb_node")
class MongoDBNode(BaseNode):
    """
    MongoDB NoSQL database integration.
    """
    node_type = "mongodb_node"
    version = "1.0.0"
    category = "database"
    credentials_required = ["mongodb_auth"]

    inputs = {
        "action": {
            "type": "dropdown",
            "default": "find",
            "options": ["find", "insert_one", "update_one", "delete_one"],
            "description": "MongoDB action"
        },
        "collection": {
            "type": "string",
            "optional": True
        },
        "query": {
            "type": "string",
            "optional": True,
            "description": "JSON Query Filter"
        },
        "document": {
            "type": "string",
            "optional": True,
            "description": "JSON Document"
        }
    }

    outputs = {
        "result": {"type": "any"},
        "status": {"type": "string"}
    }

    async def execute(self, input_data: Any, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        try:
            import motor.motor_asyncio
        except ImportError:
            return {"status": "error", "error": "motor library not installed. Please install it to use MongoDB Node."}

        try:
            creds = await self.get_credential("mongodb_auth")
            uri = creds.get("connection_string", "mongodb://localhost:27017")
            db_name = creds.get("database")
            
            client = motor.motor_asyncio.AsyncIOMotorClient(uri)
            db = client[db_name]
            
            action = self.get_config("action", "find")
            collection_name = self.get_config("collection")
            if not collection_name: 
                 return {"status": "error", "error": "collection required"}
            
            coll = db[collection_name]

            import json
            
            if action == "find":
                query_str = self.get_config("query", "{}")
                try:
                    query = json.loads(query_str)
                except:
                    return {"status": "error", "error": "Invalid JSON in query"}
                
                cursor = coll.find(query)
                docs = await cursor.to_list(length=100) # Limit default
                # Simplify types like ObjectId to string
                for doc in docs:
                   if "_id" in doc: doc["_id"] = str(doc["_id"])
                   
                return {"status": "success", "data": {"result": docs}}
            
            elif action == "insert_one":
                doc_str = self.get_config("document")
                if not doc_str: return {"status": "error", "error": "document required"}
                try:
                    doc = json.loads(doc_str)
                except:
                    return {"status": "error", "error": "Invalid JSON in document"}
                    
                res = await coll.insert_one(doc)
                return {"status": "success", "data": {"result": str(res.inserted_id)}}
            
            return {"status": "error", "error": f"Unsupported action: {action}"}

        except Exception as e:
            return {"status": "error", "error": f"MongoDB Node Failed: {str(e)}"}
