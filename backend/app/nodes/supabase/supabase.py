from langchain_community.vectorstores import SupabaseVectorStore
from supabase.client import Client, create_client

from lfx.base.vectorstores.model import LCVectorStoreComponent, check_cached_vector_store
from lfx.helpers.data import docs_to_data
from lfx.io import HandleInput, IntInput, SecretStrInput, StrInput, DropdownInput
from lfx.schema.data import Data

class SupabaseVectorStoreComponent(LCVectorStoreComponent):
    display_name = "Supabase"
    description = "Supabase Vector Store with search capabilities"
    name = "SupabaseVectorStore"
    icon = "Supabase"
    
    @staticmethod
    def fetch_tables_from_supabase(base_url: str, api_key: str):
        print(f"📡 Debug: Dynamically fetching tables from {base_url}")
        import requests
        try:
            headers = {
                "apikey": api_key,
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            }
            # Query Postgrest OpenAPI spec for definitions (table names)
            endpoint = f"{base_url.rstrip('/')}/rest/v1/"
            response = requests.get(endpoint, headers=headers, timeout=5)
            
            if response.status_code == 200:
                data = response.json()
                tables = list(data.get("definitions", {}).keys())
                print(f"✅ Found tables: {tables}")
                return tables
            
            # Fallback to hardcoded list if discovery fails
            return ["test", "documents", "vectors", "embeddings"]
        except Exception as e:
             print(f"❌ Error fetching tables: {str(e)}")
             return ["test", "documents", "vectors", "embeddings"]

    inputs = [
        StrInput(name="supabase_url", display_name="Supabase URL", required=True),
        SecretStrInput(name="supabase_service_key", display_name="Supabase Service Key", required=True),
        DropdownInput(
            name="table_name", 
            display_name="Table Name", 
            advanced=False, 
            options=[], 
            real_time_refresh=True
        ),
        StrInput(name="query_name", display_name="Query Name"),
        *LCVectorStoreComponent.inputs,
        HandleInput(name="embedding", display_name="Embedding", input_types=["Embeddings"]),
        IntInput(
            name="number_of_results",
            display_name="Number of Results",
            info="Number of results to return.",
            value=4,
            advanced=True,
        ),
    ]

    @check_cached_vector_store
    def build_vector_store(self) -> SupabaseVectorStore:
        supabase: Client = create_client(self.supabase_url, supabase_key=self.supabase_service_key)

        # Convert DataFrame to Data if needed using parent's method
        self.ingest_data = self._prepare_ingest_data()

        documents = []
        for _input in self.ingest_data or []:
            if isinstance(_input, Data):
                documents.append(_input.to_lc_document())
            elif isinstance(_input, dict):
                # If it's a raw dict (like from Docling), wrap it in a Document
                from langchain_core.documents import Document
                content = _input.get("text") or _input.get("content") or str(_input)
                metadata = _input.get("metadata") or {k: v for k, v in _input.items() if k not in ["text", "content"]}
                documents.append(Document(page_content=content, metadata=metadata))
            else:
                documents.append(_input)

        if documents:
            supabase_vs = SupabaseVectorStore.from_documents(
                documents=documents,
                embedding=self.embedding,
                query_name=self.query_name,
                client=supabase,
                table_name=self.table_name,
            )
        else:
            supabase_vs = SupabaseVectorStore(
                client=supabase,
                embedding=self.embedding,
                table_name=self.table_name,
                query_name=self.query_name,
            )

        return supabase_vs

    def search_documents(self) -> list[Data]:
        vector_store = self.build_vector_store()

        if self.search_query and isinstance(self.search_query, str) and self.search_query.strip():
            docs = vector_store.similarity_search(
                query=self.search_query,
                k=self.number_of_results,
            )

            data = docs_to_data(docs)
            self.status = data
            return data
        return []
