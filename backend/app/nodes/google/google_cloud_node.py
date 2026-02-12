from typing import Any, Dict, Optional, List
from ..base import BaseNode
from ..registry import register_node
import json

@register_node("google_cloud_action")
class GoogleCloudNode(BaseNode):
    """
    Unified Node for Google Cloud Platform (BigQuery, Storage, Compute).
    """
    node_type = "google_cloud_action"
    version = "1.0.0"
    category = "infrastructure"
    credentials_required = ["gcp_auth"]

    inputs = {
        "service": {"type": "string", "default": "bigquery", "enum": ["bigquery", "storage", "compute"]},
        "action": {"type": "string", "default": "query", "enum": ["query", "upload", "stop_instance", "list_resources"]},
        "query": {"type": "string", "optional": True},
        "resource_id": {"type": "string", "optional": True}
    }
    outputs = {
        "results": {"type": "any"},
        "status": {"type": "string"}
    }

    async def execute(self, input_data: Any, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        try:
            # 1. Resolve Auth
            creds = await self.get_credential("gcp_auth")
            project_id = creds.get("project_id") or self.get_config("project_id")
            
            if not project_id:
                return {"status": "error", "error": "GCP Project ID is required."}

            service = self.get_config("service", "bigquery")
            action = self.get_config("action", "query")

            if service == "bigquery":
                if action == "query":
                    sql = str(input_data) if isinstance(input_data, str) else self.get_config("query")
                    if not sql:
                         return {"status": "error", "error": "SQL Query is required for BigQuery."}
                    
                    # Simulation
                    return {
                        "status": "success",
                        "data": {
                            "results": [
                                {"id": 1, "user": "alice", "spend": 45.0},
                                {"id": 2, "user": "bob", "spend": 22.5}
                            ],
                            "row_count": 2
                        }
                    }

            elif service == "storage":
                return {
                    "status": "success",
                    "data": {"bucket": "studio-data", "status": "resource_listed"}
                }

            return {"status": "error", "error": f"Unsupported GCP service/action: {service}/{action}"}

        except Exception as e:
            return {"status": "error", "error": f"Google Cloud Node Error: {str(e)}"}
