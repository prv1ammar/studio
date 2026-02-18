from typing import Any, Dict, Optional, List
from ..base import BaseNode
from ..registry import register_node
from supabase import create_client

@register_node("supabase_action")
class SupabaseActionNode(BaseNode):
    """
    Automate database actions in Supabase (Select, Insert, etc.).
    """
    node_type = "supabase_action"
    version = "1.0.0"
    category = "storage"
    credentials_required = ["supabase_auth"]


    properties = [
        {
            'displayName': 'Operation',
            'name': 'operation',
            'type': 'string',
            'default': 'select',
        },
        {
            'displayName': 'Data',
            'name': 'data',
            'type': 'string',
            'default': '',
            'description': 'Query or record data',
        },
        {
            'displayName': 'Table Name',
            'name': 'table_name',
            'type': 'string',
            'default': '',
            'description': 'Database table name',
        },
    ]
    inputs = {
        "action": {"type": "string", "default": "select", "enum": ["select", "insert"]},
        "table_name": {"type": "string", "description": "Database table name"},
        "data": {"type": "object", "optional": True, "description": "Query or record data"}
    }
    outputs = {
        "results": {"type": "array"},
        "status": {"type": "string"}
    }

    async def execute(self, input_data: Any, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        try:
            # 1. Resolve Auth
            creds = await self.get_credential("supabase_auth")
            url = creds.get("url") or creds.get("supabase_url") if creds else self.get_config("supabase_url")
            key = creds.get("key") or creds.get("supabase_key") if creds else self.get_config("supabase_key")
            
            if not url or not key:
                return {"status": "error", "error": "Supabase URL and Key are required."}

            client = create_client(url, key)
            action = self.get_config("action", "select")
            table = self.get_config("table_name")

            if not table:
                return {"status": "error", "error": "Table name is required."}

            if action == "select":
                # input_data can be search filters
                query = client.table(table).select("*")
                # Simple implementation: fetch all
                resp = query.execute()
                return {
                    "status": "success",
                    "data": {
                        "results": resp.data,
                        "count": len(resp.data)
                    }
                }

            elif action == "insert":
                record = input_data if isinstance(input_data, dict) else self.get_config("data")
                if not record:
                    return {"status": "error", "error": "Data record is required for insert."}
                
                resp = client.table(table).insert(record).execute()
                return {
                    "status": "success",
                    "data": {
                        "results": resp.data
                    }
                }

            return {"status": "error", "error": f"Unsupported action: {action}"}

        except Exception as e:
            return {"status": "error", "error": f"Supabase Node Error: {str(e)}"}