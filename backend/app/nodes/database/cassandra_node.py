"""
Cassandra Node - Studio Standard (Universal Method)
Batch 113: Intelligent Infrastructure & IoT
"""
from typing import Any, Dict, Optional
from ...base import BaseNode
from ...registry import register_node

@register_node("cassandra_node")
class CassandraNode(BaseNode):
    """
    Execute CQL queries in Cassandra / Astra DB.
    """
    node_type = "cassandra_node"
    version = "1.0.0"
    category = "database"
    credentials_required = ["cassandra_auth"]

    inputs = {
        "query": {
            "type": "string",
            "required": True,
            "description": "CQL query to execute"
        },
        "keyspace": {
            "type": "string",
            "optional": True
        }
    }

    outputs = {
        "results": {"type": "list"},
        "status": {"type": "string"}
    }

    async def execute(self, input_data: Any, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        try:
            from cassandra.cluster import Cluster
            from cassandra.auth import PlainTextAuthProvider
        except ImportError:
            return {"status": "error", "error": "cassandra-driver not installed"}

        try:
            creds = await self.get_credential("cassandra_auth")
            hosts = creds.get("hosts", "localhost").split(",")
            user = creds.get("username")
            password = creds.get("password")
            
            auth_provider = PlainTextAuthProvider(username=user, password=password) if user else None
            cluster = Cluster(hosts, auth_provider=auth_provider)
            session = cluster.connect(self.get_config("keyspace"))
            
            query = self.get_config("query") or str(input_data)
            rows = session.execute(query)
            
            results = [dict(row._asdict()) for row in rows]
            return {"status": "success", "data": {"results": results}}

        except Exception as e:
            return {"status": "error", "error": f"Cassandra failure: {str(e)}"}
        finally:
            if 'cluster' in locals(): cluster.shutdown()
