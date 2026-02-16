"""
Google BigQuery Node - Studio Standard
Batch 116: Data & Warehouse
"""
from typing import Any, Dict, Optional, List
import aiohttp
from ...base import BaseNode
from ...registry import register_node

@register_node("google_bigquery_node")
class BigQueryNode(BaseNode):
    """
    Query and manage data in Google BigQuery.
    """
    node_type = "google_bigquery_node"
    version = "1.0.0"
    category = "database"
    credentials_required = ["google_bigquery_auth"]

    inputs = {
        "action": {
            "type": "dropdown",
            "default": "query",
            "options": ["query", "list_datasets", "list_tables", "get_table_info"],
            "description": "BigQuery action"
        },
        "project_id": {
            "type": "string",
            "required": True,
            "description": "Google Cloud Project ID"
        },
        "query": {
            "type": "string",
            "optional": True,
            "description": "SQL query to execute"
        },
        "dataset_id": {
            "type": "string",
            "optional": True
        },
        "table_id": {
            "type": "string",
            "optional": True
        }
    }

    outputs = {
        "result": {"type": "any"},
        "status": {"type": "string"},
        "total_rows": {"type": "number"}
    }

    async def execute(self, input_data: Any, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        try:
            creds = await self.get_credential("google_bigquery_auth")
            access_token = creds.get("access_token")
            
            if not access_token:
                return {"status": "error", "error": "Google BigQuery access token required"}

            project_id = self.get_config("project_id")
            base_url = f"https://bigquery.googleapis.com/bigquery/v2/projects/{project_id}"
            headers = {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json"
            }
            
            action = self.get_config("action", "query")

            async with aiohttp.ClientSession() as session:
                if action == "query":
                    sql = self.get_config("query") or str(input_data)
                    if not sql:
                        return {"status": "error", "error": "SQL query required"}
                    
                    url = f"{base_url}/queries"
                    payload = {"query": sql, "useLegacySql": False}
                    
                    async with session.post(url, headers=headers, json=payload) as resp:
                        res_data = await resp.json()
                        if resp.status != 200:
                            return {"status": "error", "error": f"BigQuery Error: {res_data.get('error', {}).get('message', 'Unknown')}"}
                        
                        rows = res_data.get("rows", [])
                        return {
                            "status": "success", 
                            "data": {
                                "result": rows,
                                "total_rows": int(res_data.get("totalRows", 0)),
                                "job_complete": res_data.get("jobComplete")
                            }
                        }

                elif action == "list_datasets":
                    url = f"{base_url}/datasets"
                    async with session.get(url, headers=headers) as resp:
                        res_data = await resp.json()
                        return {"status": "success", "data": {"result": res_data.get("datasets", [])}}

            return {"status": "error", "error": f"Unsupported action: {action}"}

        except Exception as e:
            return {"status": "error", "error": f"BigQuery Node Failed: {str(e)}"}
