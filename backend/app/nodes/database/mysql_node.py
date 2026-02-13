"""
MySQL Node - Studio Standard (Universal Method)
Batch 95: Database Connectors (n8n Critical - Enhanced)
"""
from typing import Any, Dict, Optional, List
import aiomysql
from ...base import BaseNode
from ...registry import register_node

@register_node("mysql_node")
class MySQLNode(BaseNode):
    """
    Execute SQL queries on MySQL database.
    """
    node_type = "mysql_node"
    version = "1.0.0"
    category = "database"
    credentials_required = ["mysql_auth"]

    inputs = {
        "action": {
            "type": "dropdown",
            "default": "execute_query",
            "options": ["execute_query", "insert_rows", "update_rows", "delete_rows"],
            "description": "MySQL action"
        },
        "query": {
            "type": "string",
            "required": True,
            "description": "SQL query with parameters (%s, %s, etc.)"
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
            creds = await self.get_credential("mysql_auth")
            host = creds.get("host", "localhost")
            port = int(creds.get("port", 3306))
            user = creds.get("user")
            password = creds.get("password")
            db = creds.get("database")
            
            # Connect
            pool = await aiomysql.create_pool(host=host, port=port,
                                              user=user, password=password,
                                              db=db, autocommit=True)
            
            try:
                action = self.get_config("action", "execute_query")
                query = self.get_config("query")
                params_str = self.get_config("params", "[]")
                
                import json
                params = json.loads(params_str) if isinstance(params_str, str) else params_str
                if not isinstance(params, list): params = [params]
                
                async with pool.acquire() as conn:
                    async with conn.cursor(aiomysql.DictCursor) as cur:
                        if action in ["execute_query", "insert_rows", "update_rows", "delete_rows"]:
                            await cur.execute(query, tuple(params))
                            
                            if query.strip().upper().startswith("SELECT"):
                                result = await cur.fetchall()
                                return {"status": "success", "data": {"result": result}}
                            else:
                                return {"status": "success", "data": {"result": {"updated_rows": cur.rowcount, "last_id": cur.lastrowid}}}
                        
                        return {"status": "error", "error": f"Unsupported action: {action}"}

            finally:
                pool.close()
                await pool.wait_closed()

        except Exception as e:
            return {"status": "error", "error": f"MySQL Node Failed: {str(e)}"}
