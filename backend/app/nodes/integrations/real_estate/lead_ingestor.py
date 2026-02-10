from ...base import BaseNode
from ...registry import register_node
from typing import Any, Dict, Optional, List
import requests
from supabase import create_client
from langchain_community.vectorstores import SupabaseVectorStore
from langchain_core.documents import Document
import json

@register_node("leadIngestorNode")
class LeadIngestorNode(BaseNode):
    """
    Unified Ingestor Node for Real Estate Leads.
    Performs 'Dual Storage':
    1. Embeds & Stores in Supabase (Vector Search)
    2. Stores in SmartDB/NocoDB (Management)
    """

    async def execute(self, input_data: Any, context: Optional[Dict[str, Any]] = None) -> Any:
        try:
            # 1. Resolve Data
            lead_data = None
            if isinstance(input_data, dict):
                # Check if it's the output of LeadFormatter
                lead_data = input_data.get("formatted_lead") or input_data
            else:
                lead_data = input_data

            if not lead_data:
                print("⚠️ Lead Ingestor: No lead data provided.")
                return "Error: No lead data provided for ingestion."

            # 2. Get Configs (with Env fallbacks)
            import os
            # NocoDB Config
            nocodb_url = self.config.get("nocodb_url") or os.getenv("NOCODB_URL") or "https://nocodb.tybot.ma"
            nocodb_key = self.config.get("nocodb_api_key") or os.getenv("NOCODB_API_KEY") or "s-m7Ue3MzAsf7AuNrzYyhL0Oz5NQoyEuT18vcI7X"
            nocodb_project = self.config.get("nocodb_project_id") or os.getenv("NOCODB_PROJECT_ID") or "pwmt3n4wh4uubxd"
            nocodb_table = self.config.get("nocodb_table_id") or os.getenv("NOCODB_TABLE_ID") or "mkf64o30qn37uh4"

            # Supabase Config
            supabase_url = self.config.get("supabase_url") or os.getenv("SUPABASE_URL") or "https://vvqbtimkusvbujuocgbg.supabase.co"
            supabase_key = self.config.get("supabase_service_key") or os.getenv("SUPABASE_SERVICE_KEY") or "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InZ2cWJ0aW1rdXN2YnVqdW9jZ2JnIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc2ODMwMTk1MCwiZXhwIjoyMDgzODc3OTUwfQ.EmiTItlzYA0eHBFFAWy8_5zAu37notDOtkee6h0w8Jk"
            supabase_table = self.config.get("supabase_table_name") or os.getenv("SUPABASE_TABLE_NAME") or "properties"

            # 3. Resolve Embedding Model from Graph
            embedding_model = None
            if context and "graph_data" in context:
                graph = context["graph_data"]
                node_id = context["node_id"]
                edges = graph.get("edges", [])
                nodes = graph.get("nodes", [])
                
                embedding_edge = next((e for e in edges if e["target"] == node_id and e["targetHandle"] == "embedding"), None)
                if embedding_edge:
                    from ...factory import NodeFactory
                    source_id = embedding_edge["source"]
                    source_node = next((n for n in nodes if n["id"] == source_id), None)
                    if source_node:
                        factory = NodeFactory()
                        emb_node = factory.get_node(source_node["data"].get("id"), source_node["data"])
                        embedding_model = await emb_node.get_langchain_object(context)

            # 4. Step 1: Insert into SmartDB (NocoDB)
            results = {"smartdb": None, "supabase": None}
            
            if nocodb_url and nocodb_key and nocodb_project and nocodb_table:
                print(f"📡 SmartDB (Dual): Inserting lead into {nocodb_table}...")
                headers = {"xc-token": nocodb_key, "Content-Type": "application/json"}
                endpoint = f"{nocodb_url.rstrip('/')}/api/v1/db/data/noco/{nocodb_project}/{nocodb_table}"
                
                # Ensure lead_data is a dictionary for NocoDB
                noco_data = lead_data if isinstance(lead_data, dict) else {"content": str(lead_data)}
                
                resp = requests.post(endpoint, headers=headers, json=noco_data, timeout=10)
                if resp.status_code in [200, 201]:
                    results["smartdb"] = "Success"
                    print("✅ SmartDB: Lead stored successfully.")
                else:
                    results["smartdb"] = f"Failed ({resp.status_code})"
                    print(f"❌ SmartDB Error: {resp.text}")
            else:
                print(f"⚠️ SmartDB Skip: Config missing (url={bool(nocodb_url)}, table={bool(nocodb_table)})")

            # 5. Step 2: Ingest into Supabase (Vector Store)
            if supabase_url and supabase_key and supabase_table and embedding_model:
                print(f"📡 Supabase (Dual): Vectorizing and storing lead in {supabase_table}...")
                
                try:
                    # Create text content for embedding
                    content_parts = []
                    if isinstance(lead_data, dict):
                        if lead_data.get("location"): content_parts.append(f"Location: {lead_data['location']}")
                        if lead_data.get("property_type"): content_parts.append(f"Type: {lead_data['property_type']}")
                        if lead_data.get("price"): content_parts.append(f"Price: {lead_data['price']} DH")
                        if lead_data.get("description"): content_parts.append(f"Description: {lead_data['description']}")
                        if lead_data.get("bedrooms"): content_parts.append(f"Bedrooms: {lead_data['bedrooms']}")
                        
                        text_content = " | ".join(content_parts) if content_parts else json.dumps(lead_data)
                    else:
                        text_content = str(lead_data)
                    
                    client = create_client(supabase_url, supabase_key)
                    
                    # Generate embedding manually using the model
                    vector = embedding_model.embed_query(text_content)
                    
                    # Prepare the final payload for Supabase (Matching seed_data.py schema)
                    supabase_payload = {
                        "title": f"{lead_data.get('property_type', 'Property')} in {lead_data.get('location', 'Morocco')}",
                        "description": lead_data.get("description", text_content),
                        "price": lead_data.get("price"),
                        "location": lead_data.get("location"),
                        "bedrooms": lead_data.get("bedrooms"),
                        "surface_m2": lead_data.get("surface_m2"),
                        "property_type": lead_data.get("property_type"),
                        "status": "available",
                        "embedding": vector
                    }

                    # PERFROM MANUAL INSERT
                    print(f"🚀 Supabase Manual Insert: Sending to table '{supabase_table}'...")
                    insert_resp = client.table(supabase_table).insert(supabase_payload).execute()
                    
                    results["supabase"] = "Success"
                    print("✅ Supabase: Lead vectorized and stored successfully.")
                except Exception as ve:
                    print(f"❌ Supabase Vector Store Error: {ve}")
                    results["supabase"] = f"Failed ({str(ve)})"
            else:
                print(f"⚠️ Supabase Skip: url={bool(supabase_url)}, key={bool(supabase_key)}, table={bool(supabase_table)}, model={bool(embedding_model)}")
                if not embedding_model:
                    results["supabase"] = "Failed (No Embedding Model connected)"
                else:
                    results["supabase"] = "Failed (Missing Config)"

            summary = f"Lead Ingestion Summary:\n- SmartDB: {results['smartdb']}\n- Supabase: {results['supabase']}"
            print(f"📋 Ingestion Summary: {summary}")
            
            return {
                "status": summary,
                "data": lead_data,
                "results": results
            }

        except Exception as e:
            print(f"❌ Lead Ingestor Cluster Failure: {e}")
            import traceback
            traceback.print_exc()
            return {"error": str(e), "status": "failed"}

    async def get_langchain_object(self, context: Optional[Dict[str, Any]] = None) -> Any:
        # This node can also act as a tool for an agent
        from langchain_classic.tools import Tool
        
        def run_tool(query: str):
            import asyncio
            import json
            
            try:
                params = json.loads(query)
                data = params.get("data", params)
                
                # Dynamic override from Agent
                if "noco_table" in params:
                    self.config["nocodb_table_id"] = params["noco_table"]
                if "supabase_table" in params:
                    self.config["supabase_table_name"] = params["supabase_table"]
                    
            except:
                data = query
                
            result = asyncio.run(self.execute(data, context))
            if isinstance(result, dict) and "status" in result:
                return result["status"]
            return str(result)

        return Tool(
            name="agent_content_dual_ingest",
            description="Unified STORAGE tool. Input: JSON with 'data' and optional 'noco_table'/'supabase_table'. Automatically embeds for search and adds to DB.",
            func=run_tool
        )
