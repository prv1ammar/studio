from ..base import BaseNode
from ..registry import register_node
from typing import Any, Dict, Optional, List
import aiohttp
import json
from supabase import create_client
from langchain_community.vectorstores import SupabaseVectorStore
from langchain_core.documents import Document

@register_node("dualIngestorNode")
class DualIngestorNode(BaseNode):
    """
    Generalized Dual Storage Ingestor.
    Saves data to both a SQL-like store (NocoDB/SmartDB) and a Vector Store (Supabase).
    """

    async def execute(self, input_data: Any, context: Optional[Dict[str, Any]] = None) -> Any:
        try:
            # 1. Resolve Data
            data = input_data if input_data else {}
            if not isinstance(data, dict):
                data = {"content": str(data)}

            # 2. Configuration
            # NocoDB Config
            nocodb_url = self.config.get("nocodb_url")
            nocodb_key = self.config.get("nocodb_api_key")
            nocodb_project = self.config.get("nocodb_project_id")
            nocodb_table = self.config.get("nocodb_table_id")

            # Supabase Config
            supabase_url = self.config.get("supabase_url")
            supabase_key = self.config.get("supabase_service_key")
            supabase_table = self.config.get("supabase_table_name")
            
            # Content Schema (which fields to embed)
            content_fields = self.config.get("content_fields", "").split(",")
            content_fields = [f.strip() for f in content_fields if f.strip()]

            # 3. Resolve Embedding Model
            embedding_model = None
            if context and "graph_data" in context:
                from ..factory import NodeFactory
                graph = context["graph_data"]
                node_id = context["node_id"]
                edges = graph.get("edges", [])
                nodes = graph.get("nodes", [])
                
                embedding_edge = next((e for e in edges if e["target"] == node_id and e["targetHandle"] == "embedding"), None)
                if embedding_edge:
                    source_id = embedding_edge["source"]
                    source_node = next((n for n in nodes if n["id"] == source_id), None)
                    if source_node:
                        factory = NodeFactory()
                        emb_node = factory.get_node(source_node["data"].get("id"), source_node["data"])
                        embedding_model = await emb_node.get_langchain_object(context)

            results = {"smartdb": "Skipped", "supabase": "Skipped"}

            # 4. Storage 1: NocoDB
            if nocodb_url and nocodb_key and nocodb_project and nocodb_table:
                async with aiohttp.ClientSession() as session:
                    headers = {"xc-token": nocodb_key, "Content-Type": "application/json"}
                    endpoint = f"{nocodb_url.rstrip('/')}/api/v1/db/data/noco/{nocodb_project}/{nocodb_table}"
                    async with session.post(endpoint, headers=headers, json=data) as resp:
                        if resp.status in [200, 201]:
                            results["smartdb"] = "Success"
                        else:
                            txt = await resp.text()
                            results["smartdb"] = f"Error ({resp.status}): {txt}"

            # 5. Storage 2: Supabase Vector Store
            if supabase_url and supabase_key and supabase_table and embedding_model:
                # Build text content for embedding
                if content_fields:
                    text_content = " | ".join([f"{f}: {data.get(f)}" for f in content_fields if data.get(f)])
                else:
                    text_content = json.dumps(data)

                client = create_client(supabase_url, supabase_key)
                doc = Document(page_content=text_content, metadata=data)
                
                # Note: Testing in async environment might require care with LangChain's sync methods
                # but many vectorstores are fine. 
                SupabaseVectorStore.from_documents(
                    [doc],
                    embedding_model,
                    client=client,
                    table_name=supabase_table,
                    query_name=self.config.get("supabase_query_name", "match_documents")
                )
                results["supabase"] = "Success"

            return {
                "status": "completed",
                "summary": results,
                "data": data
            }

        except Exception as e:
            return {"error": str(e), "status": "failed"}

    async def get_langchain_object(self, context: Optional[Dict[str, Any]] = None) -> Any:
        return None
