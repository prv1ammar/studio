import json
import requests
from ...base import BaseNode
from ...registry import register_node
from typing import Any, Dict, Optional, List
from langchain_core.tools import Tool

class NocoDBAPIWrapper:
    def __init__(self, base_url: str, api_key: str):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key

    def _get_headers(self):
        return {
            "xc-token": self.api_key,
            "xc-auth": self.api_key, # Try both common headers
            "Content-Type": "application/json"
        }

    def fetch_projects(self):
        # NocoDB V1 for projects
        url = f"{self.base_url}/api/v1/db/meta/projects"
        print(f"📡 NocoDB API: Fetching Projects from {url}")
        try:
            response = requests.get(url, headers=self._get_headers(), timeout=10)
            if response.status_code != 200:
                 # Try V2 projects path if V1 fails
                 url = f"{self.base_url}/api/v2/meta/bases"
                 print(f"📡 NocoDB API: Trying V2 Bases {url}")
                 response = requests.get(url, headers=self._get_headers(), timeout=10)
            
            response.raise_for_status()
            data = response.json()
            return data.get("list", data) if isinstance(data, dict) else data
        except Exception as e:
            print(f"❌ NocoDB API Error: {e}")
            return []

    def fetch_tables(self, project_id: str):
        # NocoDB V2 for tables
        url = f"{self.base_url}/api/v2/meta/bases/{project_id}/tables"
        print(f"📡 NocoDB API: Fetching Tables from {url}")
        response = requests.get(url, headers=self._get_headers(), timeout=10)
        
        if response.status_code != 200:
             # Try V1 path fallback
             url = f"{self.base_url}/api/v1/db/meta/projects/{project_id}/tables"
             print(f"📡 NocoDB API: Trying V1 Tables {url}")
             response = requests.get(url, headers=self._get_headers(), timeout=10)

        print(f"📥 NocoDB API: Status {response.status_code}")
        response.raise_for_status()
        data = response.json()
        return data.get("list", data) if isinstance(data, dict) else data

    def run_query(self, project_id: str, table_id: str, operation: str, data: Any = None) -> Any:
        """Run CRUD operations."""
        import json
        if isinstance(data, str):
            try:
                data = json.loads(data)
            except:
                pass # Keep as string if not JSON

        base = self.base_url
        endpoint = f"{base}/api/v1/db/data/noco/{project_id}/{table_id}"
        
        # Robust operation normalization
        op_norm = str(operation).strip().lower()
        print(f"📡 NocoDB API Query: {operation} (Norm: {op_norm}) on {endpoint}")
        
        # Determine method
        if op_norm in ["read", "all", "list", "search"]:
            params = data if isinstance(data, dict) else {}
            
            # AUTOMATIC FILTER CONVERSION: If agent sends {"filters": {...}}, convert to NocoDB 'where'
            if "filters" in params and isinstance(params["filters"], dict):
                filters = params.pop("filters")
                where_clauses = []
                
                # Column Alias Mapping (Natural Language -> Database Column)
                aliases = {
                    "type": "property_type",
                    "kind": "property_type",
                    "property_type": "property_type",
                    "address": "location",
                    "location": "location",
                    "city": "location",
                    "area": "location",
                    "surface": "surface_m2",
                    "m2": "surface_m2"
                }

                for k, v in filters.items():
                    # Apply alias if exists
                    actual_key = aliases.get(k.lower(), k)
                    where_clauses.append(f"({actual_key},like,%{v}%)")
                
                if where_clauses:
                    params["where"] = "~and".join(where_clauses)
            
            response = requests.get(endpoint, headers=self._get_headers(), params=params, timeout=30)
        elif op_norm == "create":
            response = requests.post(endpoint, headers=self._get_headers(), json=data)
        elif op_norm == "update":
            row_id = data.get("id") if isinstance(data, dict) else None
            if not row_id: raise ValueError("ID required for Update")
            response = requests.patch(f"{endpoint}/{row_id}", headers=self._get_headers(), json=data)
        elif op_norm == "delete":
            row_id = data if not isinstance(data, dict) else data.get("id")
            if not row_id: raise ValueError("ID required for Delete")
            response = requests.delete(f"{endpoint}/{row_id}", headers=self._get_headers())
        else:
            raise ValueError(f"Unsupported operation: {operation}")
            
        print(f"📥 NocoDB API Query: Status {response.status_code}")
        response.raise_for_status()
        return response.json()

@register_node("smartDB")
class SmartDBNode(BaseNode):
    """
    NocoDB SmartDB Node powered by LangChain.
    """
    async def execute(self, input_data: Any, context: Optional[Dict[str, Any]] = None) -> Any:
        try:
            tool = await self.get_langchain_object(context)
            if isinstance(tool, str): return tool # Error message
            
            # Simple wrapper to handle calling generated tool from the node directly
            if isinstance(tool, list) and tool:
                 # Use the first read-like tool if multiple
                 target = next((t for t in tool if "read" in t.name or "all" in t.name), tool[0])
                 return target.run(input_data)
            
            return tool.run(input_data)
        except Exception as e:
            return f"SmartDB Error: {str(e)}"

    async def get_langchain_object(self, context: Optional[Dict[str, Any]] = None) -> Any:
        try:
            base_url = self.config.get("base_url", "").strip()
            api_key = self.config.get("api_key", "").strip()
            project_id = self.config.get("project_id", "")
            table_id = self.config.get("table_id", "")
            operation = self.config.get("operations", "Read")

            if not base_url or not api_key:
                return "Error: URL and API Key are required."

            wrapper = NocoDBAPIWrapper(base_url=base_url, api_key=api_key)

            # Resolve Labels -> IDs
            project_mapping = self.config.get("_project_mapping", [])
            for p in project_mapping:
                if p.get("label") == project_id:
                    project_id = p.get("value")
                    break
            
            table_mapping = self.config.get("_table_mapping", [])
            for t in table_mapping:
                if t.get("label") == table_id:
                    table_id = t.get("value")
                    break

            if not project_id:
                return "Error: Database must be selected."

            # Fetch all tables first
            all_tables = wrapper.fetch_tables(project_id)
            if not all_tables:
                return f"Error: No tables found in project {project_id}."

            selected_ids = []
            if isinstance(table_id, list):
                selected_ids = [str(i) for i in table_id]
            elif isinstance(table_id, str) and table_id and table_id.lower() != "all":
                selected_ids = [table_id]
            
            if selected_ids:
                target_tables = [t for t in all_tables if str(t.get("id")) in selected_ids or str(t.get("title")) in selected_ids]
            else:
                target_tables = all_tables

            tools = []
            for t in target_tables:
                tid = str(t.get("id") or t.get("table_name") or "")
                ttitle = t.get("title") or t.get("table_name") or t.get("name") or tid
                if not tid: continue
                
                def create_query_func(pid, tbl_id, op):
                    return lambda q: wrapper.run_query(pid, tbl_id, op, q)

                tool_name = f"nocodb_{operation.lower()}_{ttitle.replace(' ', '_').replace('-', '_').lower()}"
                import re
                tool_name = re.sub(r'[^a-zA-Z0-9_]', '', tool_name)
                
                if any(tool.name == tool_name for tool in tools):
                    tool_name = f"{tool_name}_{tid}"

                description = f"Perform {operation} on NocoDB table '{ttitle}'. Input: dictionary with filters/data."
                
                tools.append(Tool(
                    name=tool_name,
                    description=description,
                    func=create_query_func(project_id, tid, operation)
                ))
            
            return tools if tools else "No tables matched."
        except Exception as e:
            return f"Error building tool: {str(e)}"

    @staticmethod
    def fetch_projects(base_url: str, api_key: str):
        try:
            wrapper = NocoDBAPIWrapper(base_url=base_url, api_key=api_key)
            projects = wrapper.fetch_projects()
            results = []
            for p in projects:
                label = p.get("base_name") or p.get("title") or p.get("name") or "Unknown"
                value = p.get("base_id") or str(p.get("id"))
                results.append({"label": label, "value": value})
            return results
        except Exception as e:
            return []

    @staticmethod
    def fetch_tables(base_url: str, api_key: str, project_id: str):
        try:
            wrapper = NocoDBAPIWrapper(base_url=base_url, api_key=api_key)
            tables = wrapper.fetch_tables(project_id)
            return [{"label": t.get("table_name") or t.get("title") or t.get("name", "Unknown"), "value": str(t.get("id"))} for t in tables]
        except Exception as e:
            return []
