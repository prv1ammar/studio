from typing import Any, Dict, Optional, List
from ..base import BaseNode
from ..registry import register_node
import sqlalchemy
from sqlalchemy import text, create_engine
import os

class DatabaseBaseNode(BaseNode):
    """Base class for SQL database nodes to share connection logic."""
    category = "storage"
    version = "1.0.0"
    credentials_required = ["database_url"]

    async def _get_engine(self):
        # 1. Try Credentials
        creds = await self.get_credential("credentials_id")
        db_url = creds.get("database_url") if creds else None
        
        # 2. Fallback to config or ENV
        if not db_url:
            db_url = self.get_config("database_url") or os.getenv("DATABASE_URL")
            
        if not db_url:
            raise ValueError("Database URL is required. Provide it in credentials, config, or DATABASE_URL env.")
            
        return create_engine(db_url)

@register_node("database_query")
class DatabaseQueryNode(DatabaseBaseNode):
    """Executes a SQL SELECT query and returns rows as a list of dictionaries."""
    node_type = "database_query"
    inputs = {
        "query": {"type": "string", "description": "SQL SELECT query"},
        "params": {"type": "object", "default": {}, "description": "Query parameters"}
    }
    outputs = {
        "results": {"type": "list", "description": "List of rows as dictionaries"},
        "count": {"type": "number"},
        "status": {"type": "string"}
    }

    async def execute(self, input_data: Any, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        try:
            engine = await self._get_engine()
            query_str = self.get_config("query") or (input_data if isinstance(input_data, str) else "")
            params = self.get_config("params", {})
            
            if not query_str:
                return {"status": "error", "error": "SQL Query is required."}
            
            # Safety check (extremely basic)
            if not query_str.strip().lower().startswith("select"):
                if not self.get_config("allow_unsafe_queries"):
                    return {"status": "error", "error": "Only SELECT queries are allowed in Query Node for safety. Use Insert/Update nodes for mutations."}
            
            with engine.connect() as conn:
                result = conn.execute(text(query_str), params)
                rows = [dict(row._mapping) for row in result]
                
            return {
                "status": "success",
                "data": {
                    "results": rows,
                    "count": len(rows)
                }
            }
        except Exception as e:
            return {"status": "error", "error": f"Database Query Failed: {str(e)}"}

@register_node("database_insert")
class DatabaseInsertNode(DatabaseBaseNode):
    """Inserts a dictionary of data into a specified table."""
    node_type = "database_insert"
    inputs = {
        "table": {"type": "string", "description": "Table name"},
        "data": {"type": "object", "description": "Dictionary of column:value"}
    }
    outputs = {
        "success": {"type": "boolean"},
        "status": {"type": "string"}
    }

    async def execute(self, input_data: Any, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        try:
            engine = await self._get_engine()
            table = self.get_config("table")
            data = self.get_config("data") or (input_data if isinstance(input_data, dict) else {})
            
            if not table or not data:
                return {"status": "error", "error": "Table name and data dictionary are required."}
            
            columns = ", ".join(data.keys())
            placeholders = ", ".join([f":{k}" for k in data.keys()])
            query = f"INSERT INTO {table} ({columns}) VALUES ({placeholders})"
            
            with engine.begin() as conn:
                conn.execute(text(query), data)
                
            return {"status": "success", "data": {"success": True}}
        except Exception as e:
            return {"status": "error", "error": f"Database Insert Failed: {str(e)}"}

@register_node("database_update")
class DatabaseUpdateNode(DatabaseBaseNode):
    """Updates rows in a specified table based on a WHERE clause."""
    node_type = "database_update"
    inputs = {
        "table": {"type": "string", "description": "Table name"},
        "data": {"type": "object", "description": "Dictionary of column:value to set"},
        "where": {"type": "string", "description": "WHERE clause (e.g. id = :id_param)"},
        "params": {"type": "object", "description": "Parameters for the WHERE clause"}
    }
    outputs = {
        "success": {"type": "boolean"},
        "status": {"type": "string"}
    }

    async def execute(self, input_data: Any, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        try:
            engine = await self._get_engine()
            table = self.get_config("table")
            data = self.get_config("data") or (input_data if isinstance(input_data, dict) else {})
            where = self.get_config("where")
            params = self.get_config("params", {})
            
            if not table or not data or not where:
                return {"status": "error", "error": "Table, data, and where clause are required."}
            
            set_clause = ", ".join([f"{k} = :val_{k}" for k in data.keys()])
            query = f"UPDATE {table} SET {set_clause} WHERE {where}"
            
            # Combine params with prefixed data keys to avoid collision with 'where' params
            exec_params = {f"val_{k}": v for k, v in data.items()}
            exec_params.update(params)
            
            with engine.begin() as conn:
                conn.execute(text(query), exec_params)
                
            return {"status": "success", "data": {"success": True}}
        except Exception as e:
            return {"status": "error", "error": f"Database Update Failed: {str(e)}"}
