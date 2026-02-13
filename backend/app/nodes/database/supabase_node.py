"""
Supabase Database Node - Studio Standard
Batch 41: Database Actions
"""
from typing import Any, Dict, Optional, List
import json
from ...base import BaseNode
from ...registry import register_node

@register_node("supabase_db")
class SupabaseDBNode(BaseNode):
    """
    Perform CRUD operations on Supabase tables.
    Supports: Select, Insert, Update, Delete.
    """
    node_type = "supabase_db"
    version = "1.0.0"
    category = "database"
    credentials_required = ["supabase_auth"]

    inputs = {
        "operation": {
            "type": "dropdown",
            "default": "select",
            "options": ["select", "insert", "update", "delete", "rpc"],
            "description": "Database operation"
        },
        "table_name": {
            "type": "string",
            "required": True,
            "description": "Target table name"
        },
        "match_field": {
            "type": "string",
            "description": "Field to match for Update/Delete (e.g., 'id')"
        },
        "match_value": {
            "type": "string",
            "description": "Value to match for Update/Delete"
        },
        "columns": {
            "type": "string",
            "default": "*",
            "description": "Columns to select (comma separated)"
        },
        "data": {
            "type": "json",
            "description": "Data payload for Insert/Update/RPC"
        },
        "limit": {
            "type": "number",
            "default": 10,
            "description": "Limit results for Select"
        }
    }

    outputs = {
        "data": {"type": "array"},
        "count": {"type": "number"},
        "error": {"type": "string"}
    }

    async def execute(self, input_data: Any, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        try:
            # Check dependency
            try:
                from supabase import create_client, Client
            except ImportError:
                return {"status": "error", "error": "supabase not installed. Run: pip install supabase"}

            # Get Creds
            creds = await self.get_credential("supabase_auth")
            url = None
            key = None

            if creds:
                url = creds.get("url") or creds.get("supabase_url")
                key = creds.get("key") or creds.get("supabase_key") or creds.get("service_role_key")
            
            # Fallback
            if not url or not key:
                url = self.get_config("supabase_url")
                key = self.get_config("supabase_key")

            if not url or not key:
                return {"status": "error", "error": "Supabase URL and Key are required."}

            supabase: Client = create_client(url, key)
            
            # Get Config
            operation = self.get_config("operation", "select")
            table = self.get_config("table_name")
            
            if not table and operation != "rpc":
                 return {"status": "error", "error": "Table name is required."}

            # Prepare Data Payload
            payload = self.get_config("data", {})
            if isinstance(input_data, dict):
                payload = input_data
            elif isinstance(input_data, list) and operation == "insert":
                payload = input_data
            
            result_data = None
            count = 0

            if operation == "select":
                columns = self.get_config("columns", "*")
                limit = int(self.get_config("limit", 10))
                
                query = supabase.table(table).select(columns).limit(limit)
                
                # Simple filtering support via match inputs
                match_field = self.get_config("match_field")
                match_value = self.get_config("match_value")
                if match_field and match_value:
                    query = query.eq(match_field, match_value)
                
                response = query.execute()
                result_data = response.data
                count = len(result_data)

            elif operation == "insert":
                if not payload:
                     return {"status": "error", "error": "Data payload required for insert."}
                
                response = supabase.table(table).insert(payload).execute()
                result_data = response.data
                count = len(result_data)

            elif operation == "update":
                match_field = self.get_config("match_field")
                match_value = self.get_config("match_value")
                
                if not match_field or not match_value:
                     return {"status": "error", "error": "Match Field and Value required for update."}
                
                if not payload:
                     return {"status": "error", "error": "Data payload required for update."}

                response = supabase.table(table).update(payload).eq(match_field, match_value).execute()
                result_data = response.data
                count = len(result_data)

            elif operation == "delete":
                match_field = self.get_config("match_field")
                match_value = self.get_config("match_value")
                
                if not match_field or not match_value:
                     return {"status": "error", "error": "Match Field and Value required for delete."}

                response = supabase.table(table).delete().eq(match_field, match_value).execute()
                result_data = response.data
                count = len(result_data)

            elif operation == "rpc":
                rpc_name = self.get_config("table_name") # Reuse table_name input for function name
                if not rpc_name:
                    return {"status": "error", "error": "RPC Function Name (in Table Name field) is required."}
                
                response = supabase.rpc(rpc_name, payload).execute()
                result_data = response.data
                # RPC response structure varies, handled generically
                count = 1 if result_data else 0

            else:
                 return {"status": "error", "error": f"Unknown operation: {operation}"}

            return {
                "status": "success",
                "data": {
                    "data": result_data,
                    "count": count
                }
            }

        except Exception as e:
            return {"status": "error", "error": f"Supabase Operation Failed: {str(e)}"}
