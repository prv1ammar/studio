"""
Snowflake Node - Studio Standard (Universal Method)
Batch 95: Database Connectors (n8n Critical)
"""
from typing import Any, Dict, Optional, List
import snowflake.connector
from ..base import BaseNode
from ..registry import register_node

@register_node("snowflake_node")
class SnowflakeNode(BaseNode):
    """
    Execute SQL queries on Snowflake data warehouse.
    """
    node_type = "snowflake_node"
    version = "1.0.0"
    category = "database"
    credentials_required = ["snowflake_auth"]


    properties = [
        {
            'displayName': 'Operation',
            'name': 'operation',
            'type': 'options',
            'default': 'execute_query',
            'options': [
                {'name': 'Execute Query', 'value': 'execute_query'},
                {'name': 'Insert Rows', 'value': 'insert_rows'},
            ],
            'description': 'Snowflake action',
        },
        {
            'displayName': 'Query',
            'name': 'query',
            'type': 'string',
            'default': '',
            'description': 'SQL query to execute',
        },
    ]
    inputs = {
        "action": {
            "type": "dropdown",
            "default": "execute_query",
            "options": ["execute_query", "insert_rows"],
            "description": "Snowflake action"
        },
        "query": {
            "type": "string",
            "optional": True,
            "description": "SQL query to execute"
        }
    }

    outputs = {
        "result": {"type": "any"},
        "status": {"type": "string"}
    }

    async def execute(self, input_data: Any, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        try:
            # 1. Authentication
            creds = await self.get_credential("snowflake_auth")
            account = creds.get("account")
            user = creds.get("user")
            password = creds.get("password")
            role = creds.get("role")
            warehouse = creds.get("warehouse")
            database_name = creds.get("database")
            schema = creds.get("schema")
            
            if not account or not user or not password:
                return {"status": "error", "error": "Snowflake Account, User, and Password required."}

            # 2. Connect (Note: snowflake.connector is synchronous)
            conn = snowflake.connector.connect(
                user=user,
                password=password,
                account=account,
                warehouse=warehouse,
                database=database_name,
                schema=schema,
                role=role
            )
            
            cursor = conn.cursor()
            action = self.get_config("action", "execute_query")

            try:
                if action == "execute_query":
                    query = self.get_config("query") or str(input_data)
                    cursor.execute(query)
                    
                    # Fetch results if it's a SELECT query
                    if query.strip().upper().startswith("SELECT"):
                        columns = [col[0] for col in cursor.description]
                        rows = cursor.fetchall()
                        result = [dict(zip(columns, row)) for row in rows]
                        return {"status": "success", "data": {"result": result}}
                    else:
                        return {"status": "success", "data": {"result": {"message": "Query executed successfully"}}}

                elif action == "insert_rows":
                    # Placeholder for more complex insert logic
                    # Ideally would use executemany or file staging
                    query = self.get_config("query") or str(input_data)
                    cursor.execute(query)
                    return {"status": "success", "data": {"result": {"message": "Rows inserted"}}}
                
                return {"status": "error", "error": f"Unsupported action: {action}"}

            finally:
                cursor.close()
                conn.close()

        except Exception as e:
            return {"status": "error", "error": f"Snowflake Node Failed: {str(e)}"}