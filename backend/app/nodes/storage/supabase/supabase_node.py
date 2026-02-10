from ...base import BaseNode
from ...registry import register_node
from typing import Any, Dict, Optional
import uuid
from supabase import create_client

@register_node("supabase_SupabaseVectorStore")
class SupabaseStoreNode(BaseNode):
    async def execute(self, input_data: Any, context: Optional[Dict[str, Any]] = None) -> str:
        try:
            url = self.config.get("supabase_url")
            key = self.config.get("supabase_service_key") or self.config.get("api_key")
            table_name = self.config.get("table_name", "test")
            
            if not url or not key:
                return "Supabase Status: ⚠️ URL or Key missing in configuration."
            
            # 1. Resolve Inputs from context/graph if available
            # We prioritize "Pulling" data from handles over the sequential input_data
            data_to_ingest = None
            embedding_model = None
            
            if context and "graph_data" in context:
                graph = context["graph_data"]
                node_id = context["node_id"]
                edges = graph.get("edges", [])
                nodes = graph.get("nodes", [])
                engine = context.get("engine")
                
                # A. Pull Ingest Data
                ingest_edge = next((e for e in edges if e["target"] == node_id and e["targetHandle"] == "ingest_data"), None)
                if ingest_edge:
                    source_id = ingest_edge["source"]
                    source_node = next((n for n in nodes if n["id"] == source_id), None)
                    if source_node and engine:
                        print(f"🔄 Supabase: Pulling data from node {source_id}...")
                        data_to_ingest = await engine.execute_node(
                            source_node["data"].get("id"), 
                            None, 
                            config=source_node["data"], 
                            context={**context, "node_id": source_id}
                        )
                
                # B. Pull Embedding Model
                embedding_edge = next((e for e in edges if e["target"] == node_id and e["targetHandle"] == "embedding"), None)
                if embedding_edge:
                    from ...factory import NodeFactory
                    source_id = embedding_edge["source"]
                    source_node = next((n for n in nodes if n["id"] == source_id), None)
                    if source_node:
                        factory = NodeFactory()
                        emb_node = factory.get_node(source_node["data"].get("id"), source_node["data"])
                        embedding_model = await emb_node.get_langchain_object(context)
                
                # If we didn't pull anything, fallback to sequential input (only if it doesn't look like dummy engine data)
                if not data_to_ingest and input_data:
                     # Filter out dummy engine messages
                     if isinstance(input_data, dict) and input_data.get("content") == "Run workflow":
                         pass
                     else:
                         data_to_ingest = input_data
            
            if not embedding_model:
                return "Error: No Embedding node connected to Supabase."
            if not data_to_ingest:
                return "Supabase Status: ℹ️ No data received for ingestion. Check your connections."

            if not data_to_ingest:
                return "Supabase Status: ℹ️ No data received for ingestion."

            # 2. Perform Ingestion using SupabaseVectorStore
            from supabase import create_client
            from langchain_community.vectorstores import SupabaseVectorStore
            from langchain_core.documents import Document
            import pandas as pd
            
            supabase_client = create_client(url, key)
            
            # Normalize input data to list of Documents
            docs = []
            if isinstance(data_to_ingest, pd.DataFrame):
                for _, row in data_to_ingest.iterrows():
                    content = row.get("text") or row.get("page_content") or row.get("content") or str(row.to_dict())
                    metadata = {k: v for k, v in row.to_dict().items() if k not in ["text", "page_content", "content"]}
                    docs.append(Document(page_content=str(content), metadata=metadata))
            elif isinstance(data_to_ingest, list):
                for item in data_to_ingest:
                    if isinstance(item, dict):
                        content = item.get("text") or item.get("content") or str(item)
                        metadata = item.get("metadata") or {k: v for k, v in item.items() if k not in ["text", "content"]}
                        docs.append(Document(page_content=str(content), metadata=metadata))
                    else:
                        docs.append(Document(page_content=str(item)))
            else:
                 docs.append(Document(page_content=str(data_to_ingest)))

            if docs:
                print(f"📡 Supabase: Ingesting {len(docs)} documents into '{table_name}'...")
                SupabaseVectorStore.from_documents(
                    docs,
                    embedding_model,
                    client=supabase_client,
                    table_name=table_name,
                    query_name=self.config.get("query_name", "match_documents")
                )
                return f"✅ Success: {len(docs)} documents ingested into '{table_name}'."
            
            return "Supabase Status: ⚠️ Documents list was empty."
        except Exception as e:
            print(f"❌ Supabase Ingestion Error: {str(e)}")
            raise e

    async def get_langchain_object(self, context: Optional[Dict[str, Any]] = None) -> Any:
        from langchain_community.vectorstores import SupabaseVectorStore
        from langchain_classic.tools import Tool
        
        url = self.config.get("supabase_url")
        key = self.config.get("supabase_service_key") or self.config.get("api_key")
        table_name = self.config.get("table_name", "test")
        query_name = self.config.get("query_name", "match_documents")
        
        if not url or not key: return None

        # Resolve Embedding model from graph
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

        # Prepare tables list
        target_tables = []
        if isinstance(table_name, list):
            target_tables = [str(t) for t in table_name if t and str(t).lower() != "all"]
        elif isinstance(table_name, str) and table_name.lower() != "all":
            target_tables = [table_name]
            
        if not target_tables:
            # Fetch ALL available tables if none selected
            print(f"🔄 Supabase: No specific table selected. Fetching all available tables...")
            all_available = self.fetch_tables(url, key)
            target_tables = [t["value"] for t in all_available]
            
        if not target_tables:
            return "Error: No tables found in Supabase to generate tools."

        tools = []
        for tbl in target_tables:
            # Local copies for closure safety
            current_table = tbl
            
            def create_search_func(t_name):
                def search_func(query: str):
                    """Synchronous search function bypassing LangChain for reliability."""
                    from langchain_core.documents import Document
                    
                    print(f"🔎 Supabase Search Tool invoked for table '{t_name}' with query: '{query}'")
                    try:
                        if not embedding_model:
                            return f"Error: Search tool for {t_name} lacks a connected embedding model."
                        
                        normalized_query = query.lower().replace("graphique", "figure")
                        print("Calculating embedding...")
                        vector = embedding_model.embed_query(normalized_query)
                        
                        print(f"Connecting to Supabase and running RPC '{query_name}' on table '{t_name}'...")
                        client = create_client(url, key)
                        
                        # Direct RPC call
                        response = client.rpc(
                            query_name,
                            params={
                                "query_embedding": vector,
                                "match_threshold": 0.2,
                                "match_count": 10,
                                "table_name": t_name 
                            }
                        ).execute()
                        
                        matches = response.data
                        if not matches:
                             return f"No relevant information found in table '{t_name}'."

                        print(f"Found {len(matches)} matches in {t_name}.")
                        
                        import re
                        numbers_in_query = re.findall(r"\d+", query)
                        boosted = []
                        others = []
                        for m in matches:
                            text = (m.get("content") or m.get("text") or "").lower()
                            is_boosted = any(re.search(rf"\b{num}\b", text) for num in numbers_in_query)
                            if is_boosted: boosted.append(m)
                            else: others.append(m)
                        
                        sorted_matches = boosted + others
                        docs = []
                        for match in sorted_matches:
                            text = match.get("content") or match.get("text") or str(match)
                            docs.append(Document(page_content=text, metadata=match.get("metadata", {})))
                        
                        return "\n\n".join([f"--- Context (Table: {t_name}) ---\n{doc.page_content}" for doc in docs])
                        
                    except Exception as e:
                        print(f"🔄 Supabase Search: Primary call failed ({e}). Starting fallback chain...")
                        
                        # Fallback Chain: match_properties -> match_documents
                        fallbacks = ["match_properties", "match_documents"]
                        last_error = e
                        
                        for fallback_func in fallbacks:
                            # Try both with and without table_name parameter
                            param_variations = [
                                {"query_embedding": vector, "match_threshold": 0.2, "match_count": 10, "table_name": t_name},
                                {"query_embedding": vector, "match_threshold": 0.2, "match_count": 10}
                            ]
                            
                            for params in param_variations:
                                try:
                                    print(f"♻️ Supabase Fallback: Trying '{fallback_func}' with params {list(params.keys())}...")
                                    response = client.rpc(fallback_func, params=params).execute()
                                    matches = response.data
                                    
                                    if matches:
                                        docs = []
                                        for match in matches:
                                            text = match.get("content") or match.get("text") or str(match)
                                            docs.append(Document(page_content=text, metadata=match.get("metadata", {})))
                                        
                                        print(f"✅ Supabase Search: Success using '{fallback_func}'")
                                        return "\n\n".join([f"--- Context (Table: {t_name}) ---\n{doc.page_content}" for doc in docs])
                                    else:
                                        print(f"ℹ️ Supabase: '{fallback_func}' (params: {list(params.keys())}) returned 0 results.")
                                        # If it returned no results (but didn't error), it's a valid function but no matches.
                                        # We'll continue to see if another function/param-set finds something.
                                        
                                except Exception as fe:
                                    # print(f"⚠️ Supabase Fallback variant failed: {fe}")
                                    last_error = fe
                        
                        # If we reached here, either every attempt errored or every attempt returned 0 results.
                        # If the last_error is still the original or a generic parameter error, and we saw "0 results" somewhere, 
                        # it's better to tell the agent "no results found".
                        return f"No relevant properties found in database for '{t_name}'."
                        
                return search_func

            safe_name = current_table.replace(" ", "_").replace("-", "_").lower()
            tools.append(Tool(
                name=f"search_supabase_{safe_name}",
                description=f"Search the Supabase table '{current_table}' for information. Useful for factual questions about {current_table}.",
                func=create_search_func(current_table)
            ))
            
        print(f"✅ Supabase: Generated {len(tools)} search tools.")
        return tools

    @staticmethod
    def fetch_tables(url: str, key: str, **kwargs):
        """Fetch tables dynamically from Supabase PostgREST introspection."""
        import requests
        
        # Ensure URL points to the REST endpoint
        # Typical format: https://xyz.supabase.co/rest/v1/
        base_url = url.rstrip("/")
        if "/rest/v1" not in base_url:
            base_url = f"{base_url}/rest/v1/"
        elif not base_url.endswith("/"):
             base_url = f"{base_url}/"
            
        print(f"📡 Supabase: Introspecting tables from {base_url}")
        
        headers = {
            "apikey": key.strip(),
            "Authorization": f"Bearer {key.strip()}",
            "Content-Type": "application/json"
        }
        
        try:
            # 1. Try fetching the OpenAPI definition from root
            response = requests.get(base_url, headers=headers, timeout=10)
            
            tables = []
            
            if response.status_code == 200:
                # PostgREST returns a Swagger JSON object at the root
                data = response.json()
                definitions = data.get("definitions", {})
                
                # Each key in 'definitions' corresponds to a table/view model
                for table_name in definitions.keys():
                    # Filter out RPC functions (often starting with '(') or system definitions
                    if table_name.startswith("(") or "." in table_name:
                        continue
                    tables.append({"label": table_name, "value": table_name})
                    
                print(f"✅ Supabase Import: Found {len(tables)} tables via OpenAPI.")
            
            # 2. Fallback: If OpenAPI is disabled (common in prod), try querying information_schema via RPC?
            # Creating a generic RPC function 'get_tables' is the safest fallback if this fails.
            # But let's assume the user has standard PostgREST access.
            
            if not tables:
                print("⚠️ Supabase: No tables found via introspection. Check permissions.")
                # We return an empty list rather than hardcoded values, forcing the user to fix permissions or config.
                return []
                
            return tables
            
        except Exception as e:
            print(f"❌ Supabase Introspection Failed: {e}")
            return []
