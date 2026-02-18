"""
Clickhouse Node - Studio Standard (Universal Method)
Batch 113: Intelligent Infrastructure & IoT
"""
from typing import Any, Dict, Optional
import aiohttp
from ..base import BaseNode
from ..registry import register_node

@register_node("clickhouse_node")
class ClickhouseNode(BaseNode):
    """
    Query Clickhouse columnar database.
    """
    node_type = "clickhouse_node"
    version = "1.0.0"
    category = "database"
    credentials_required = ["clickhouse_auth"]


    properties = [
        {
            'displayName': 'Database',
            'name': 'database',
            'type': 'string',
            'default': 'default',
            'description': 'Database name',
        },
        {
            'displayName': 'Query',
            'name': 'query',
            'type': 'string',
            'default': '',
            'description': 'SQL query to execute',
            'required': True,
        },
    ]
    inputs = {
        "query": {
            "type": "string",
            "required": True,
            "description": "SQL query to execute"
        },
        "database": {
            "type": "string",
            "default": "default",
            "description": "Database name"
        }
    }

    outputs = {
        "results": {"type": "list"},
        "status": {"type": "string"}
    }

    async def execute(self, input_data: Any, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        try:
            creds = await self.get_credential("clickhouse_auth")
            host = creds.get("host", "localhost")
            port = creds.get("port", 8123)
            user = creds.get("username", "default")
            password = creds.get("password", "")
            
            query = self.get_config("query") or str(input_data)
            db = self.get_config("database", "default")

            url = f"http://{host}:{port}/"
            params = {
                "database": db,
                "query": query,
                "user": user,
                "password": password,
                "default_format": "JSON"
            }

            async with aiohttp.ClientSession() as session:
                async with session.post(url, params=params) as response:
                    if response.status != 200:
                        text = await response.text()
                        return {"status": "error", "error": f"Clickhouse Error {response.status}: {text}"}
                    
                    data = await response.json()
                    return {"status": "success", "data": {"results": data.get("data", [])}}

        except Exception as e:
            return {"status": "error", "error": f"Clickhouse Query failed: {str(e)}"}