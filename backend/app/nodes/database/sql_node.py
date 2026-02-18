"""
SQL Database Node - Studio Standard
Batch 41: Database Actions
"""
from typing import Any, Dict, Optional, List
from ..base import BaseNode
from ..registry import register_node

@register_node("sql_db")
class SQLDatabaseNode(BaseNode):
    """
    Execute SQL queries on any supported database via SQLAlchemy.
    Supports: Postgres, MySQL, SQLite, etc.
    WARNING: Use with caution. Ensure proper permissions.
    """
    node_type = "sql_db"
    version = "1.0.0"
    category = "database"
    credentials_required = ["database_url"]


    properties = [
        {
            'displayName': 'Database Url',
            'name': 'database_url',
            'type': 'string',
            'default': '',
            'description': 'Connection string (e.g., postgresql://user:pass@host:5432/db)',
        },
        {
            'displayName': 'Params',
            'name': 'params',
            'type': 'string',
            'default': '',
            'description': 'Query parameters (for safety)',
        },
        {
            'displayName': 'Query',
            'name': 'query',
            'type': 'string',
            'default': '',
            'description': 'SQL Query to execute',
            'required': True,
        },
    ]
    inputs = {
        "query": {
            "type": "string",
            "required": True,
            "description": "SQL Query to execute"
        },
        "database_url": {
            "type": "string",
            "description": "Connection string (e.g., postgresql://user:pass@host:5432/db)"
        },
        "params": {
            "type": "json",
            "optional": True,
            "description": "Query parameters (for safety)"
        }
    }

    outputs = {
        "result": {"type": "array"},
        "columns": {"type": "array"},
        "row_count": {"type": "number"}
    }

    async def execute(self, input_data: Any, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        try:
            # Check dependency
            try:
                from sqlalchemy import create_engine, text
            except ImportError:
                return {"status": "error", "error": "sqlalchemy not installed. Run: pip install sqlalchemy"}

            # Get Connect String
            conn_str = self.get_config("database_url")
            
            # Credentials override
            creds = await self.get_credential("database_url") # Generic cred name
            if creds:
                 conn_str = creds.get("url") or creds.get("connection_string")
            
            if not conn_str:
                return {"status": "error", "error": "Database URL (Connection String) is required."}

            engine = create_engine(conn_str)
            
            # Get Query
            query_str = self.get_config("query")
            if isinstance(input_data, str) and input_data:
                query_str = input_data
            
            if not query_str:
                 return {"status": "error", "error": "SQL Query is required."}

            params = self.get_config("params", {})
            if isinstance(input_data, dict):
                 params = input_data

            result_data = []
            columns = []
            row_count = 0

            # Execute
            with engine.connect() as connection:
                # Use text() to safely execute raw SQL with params
                result = connection.execute(text(query_str), params)
                
                # Check if it returns rows (SELECT) or just executes (INSERT/UPDATE)
                if result.returns_rows:
                    columns = list(result.keys())
                    rows = result.fetchall()
                    row_count = len(rows)
                    # Convert rows to dicts
                    result_data = [dict(zip(columns, row)) for row in rows]
                else:
                    row_count = result.rowcount
                    connection.commit()

            return {
                "status": "success",
                "data": {
                    "result": result_data,
                    "columns": columns,
                    "row_count": row_count
                }
            }

        except Exception as e:
            return {"status": "error", "error": f"SQL Execution Failed: {str(e)}"}