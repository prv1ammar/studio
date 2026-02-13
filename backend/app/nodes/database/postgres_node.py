"""
PostgreSQL Node - Studio Standard (Universal Method)
Batch 95: Database Connectors (n8n Critical - Enhanced)
"""
from typing import Any, Dict, Optional, List
import asyncpg
from ...base import BaseNode
from ...registry import register_node

@register_node("postgres_node")
class PostgresNode(BaseNode):
    """
    Execute SQL queries on PostgreSQL database.
    """
    node_type = "postgres_node"
    version = "1.0.0"
    category = "database"
    credentials_required = ["postgres_auth"]

    inputs = {
        "action": {
            "type": "dropdown",
            "default": "execute_query",
            "options": ["execute_query", "insert_rows", "update_rows", "delete_rows"],
            "description": "Postgres action"
        },
        "query": {
            "type": "string",
            "required": True,
            "description": "SQL query with parameters ($1, $2, etc.)"
        },
        "params": {
            "type": "string",
            "optional": True,
            "description": "JSON array of parameters"
        }
    }

    outputs = {
        "result": {"type": "any"},
        "status": {"type": "string"}
    }

    async def execute(self, input_data: Any, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        try:
            # 1. Authentication
            creds = await self.get_credential("postgres_auth")
            dsn = creds.get("connection_string")
            user = creds.get("user")
            password = creds.get("password")
            database = creds.get("database")
            host = creds.get("host")
            port = creds.get("port", 5432)
            
            # Use DSN or individual params
            conn = await asyncpg.connect(user=user, password=password, database=database, host=host, port=port)
            
            action = self.get_config("action", "execute_query")
            query = self.get_config("query")
            params_str = self.get_config("params", "[]")
            
            import json
            params = json.loads(params_str) if isinstance(params_str, str) else params_str
            if not isinstance(params, list): params = [params]
            
            try:
                if action in ["execute_query", "insert_rows", "update_rows", "delete_rows"]:
                    # asyncpg fetch returns Record objects
                    records = await conn.fetch(query, *params)
                    # Convert Records to Dict
                    results = [dict(record) for record in records]
                    return {"status": "success", "data": {"result": results}}
                
                return {"status": "error", "error": f"Unsupported action: {action}"}

            finally:
                await conn.close()

        except Exception as e:
            return {"status": "error", "error": f"Postgres Node Failed: {str(e)}"}
