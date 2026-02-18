"""
MySQL Node - Studio Standard (Universal Method)
Batch 110: Developer Tools & Databases
"""
from typing import Any, Dict, Optional
import aiohttp
from ..base import BaseNode
from ..registry import register_node

# MySQL typically requires 'aiomysql'.
# Since we are implementing parity without guaranteed drivers installed,
# we will implement the structure using `aiomysql` and handle import errors gracefully,
# or use a generic SQL interface if available.
# Decision: Use `aiomysql` as standard async driver.

@register_node("mysql_node")
class MySQLNode(BaseNode):
    """
    MySQL database integration.
    """
    node_type = "mysql_node"
    version = "1.0.0"
    category = "database"
    credentials_required = ["mysql_auth"]


    properties = [
        {
            'displayName': 'Operation',
            'name': 'operation',
            'type': 'options',
            'default': 'execute_query',
            'options': [
                {'name': 'Execute Query', 'value': 'execute_query'},
                {'name': 'Insert Row', 'value': 'insert_row'},
                {'name': 'Update Row', 'value': 'update_row'},
                {'name': 'Delete Row', 'value': 'delete_row'},
            ],
            'description': 'MySQL action',
        },
        {
            'displayName': 'Query',
            'name': 'query',
            'type': 'string',
            'default': '',
            'description': 'SQL Query',
        },
        {
            'displayName': 'Table',
            'name': 'table',
            'type': 'string',
            'default': '',
        },
    ]
    inputs = {
        "action": {
            "type": "dropdown",
            "default": "execute_query",
            "options": ["execute_query", "insert_row", "update_row", "delete_row"],
            "description": "MySQL action"
        },
        "query": {
            "type": "string",
            "optional": True,
            "description": "SQL Query"
        },
        "table": {
            "type": "string",
            "optional": True
        }
    }

    outputs = {
        "result": {"type": "any"},
        "status": {"type": "string"}
    }

    async def execute(self, input_data: Any, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        try:
            import aiomysql
        except ImportError:
            return {"status": "error", "error": "aiomysql library not installed. Please install it to use MySQL Node."}

        try:
            creds = await self.get_credential("mysql_auth")
            host = creds.get("host", "localhost")
            port = int(creds.get("port", 3306))
            user = creds.get("user")
            password = creds.get("password")
            db = creds.get("database")
            
            if not user or not db:
                return {"status": "error", "error": "MySQL user and database required"}

            pool = await aiomysql.create_pool(host=host, port=port,
                                              user=user, password=password,
                                              db=db, autocommit=True)
                                              
            action = self.get_config("action", "execute_query")

            async with pool.acquire() as conn:
                async with conn.cursor(aiomysql.DictCursor) as cur:
                    if action == "execute_query":
                        query = self.get_config("query")
                        if not query: return {"status": "error", "error": "query required"}
                        
                        await cur.execute(query)
                        result = await cur.fetchall()
                        return {"status": "success", "data": {"result": result}}
                    
                    elif action == "insert_row":
                        # Simplified insert logic
                        # Ideally takes JSON data and table
                        pass # Implementation specific to data mapping

            pool.close()
            await pool.wait_closed()
            
            return {"status": "error", "error": f"Unsupported action or NotImplemented: {action}"}

        except Exception as e:
            return {"status": "error", "error": f"MySQL Node Failed: {str(e)}"}