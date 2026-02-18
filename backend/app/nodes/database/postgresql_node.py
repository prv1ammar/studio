"""
PostgreSQL Node - Studio Standard (Universal Method)
Batch 110: Developer Tools & Databases
"""
from typing import Any, Dict, Optional
import aiohttp
from ..base import BaseNode
from ..registry import register_node

# PostgreSQL typically uses `asyncpg`.

@register_node("postgresql_node")
class PostgreSQLNode(BaseNode):
    """
    PostgreSQL database integration.
    """
    node_type = "postgresql_node"
    version = "1.0.0"
    category = "database"
    credentials_required = ["postgresql_auth"]


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
            'description': 'PostgreSQL action',
        },
        {
            'displayName': 'Query',
            'name': 'query',
            'type': 'string',
            'default': '',
            'description': 'SQL Query',
        },
    ]
    inputs = {
        "action": {
            "type": "dropdown",
            "default": "execute_query",
            "options": ["execute_query", "insert_row", "update_row", "delete_row"],
            "description": "PostgreSQL action"
        },
        "query": {
            "type": "string",
            "optional": True,
            "description": "SQL Query"
        }
    }

    outputs = {
        "result": {"type": "any"},
        "status": {"type": "string"}
    }

    async def execute(self, input_data: Any, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        try:
            import asyncpg
        except ImportError:
            return {"status": "error", "error": "asyncpg library not installed. Please install it to use PostgreSQL Node."}

        try:
            creds = await self.get_credential("postgresql_auth")
            host = creds.get("host", "localhost")
            port = int(creds.get("port", 5432))
            user = creds.get("user")
            password = creds.get("password")
            db = creds.get("database")
            
            if not user or not db:
                return {"status": "error", "error": "PostgreSQL user and database required"}

            conn = await asyncpg.connect(user=user, password=password,
                                         database=db, host=host, port=port)
                                         
            action = self.get_config("action", "execute_query")

            try:
                if action == "execute_query":
                    query = self.get_config("query")
                    if not query: return {"status": "error", "error": "query required"}
                    
                    # Fetching as records
                    records = await conn.fetch(query)
                    result = [dict(record) for record in records]
                    return {"status": "success", "data": {"result": result}}
                
                # ... insert logic simplified ... 

                return {"status": "error", "error": f"Unsupported action: {action}"}
                
            finally:
                await conn.close()

        except Exception as e:
            return {"status": "error", "error": f"PostgreSQL Node Failed: {str(e)}"}