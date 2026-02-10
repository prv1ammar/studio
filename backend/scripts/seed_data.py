import os
import asyncio
from supabase import create_client
from openai import OpenAI

# Credentials from your Studio configuration
SUPABASE_URL = "https://pbbaowiskhztxzzzflyc.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InBiYmFvd2lza2h6dHh6enpmbHljIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc2NjEyNTg4NiwiZXhwIjoyMDgxNzAxODg2fQ.odTTSAiF-iWjDhLzmMce5HaQIabCvtQEm8-r-PS6UH4"
OPENAI_API_KEY = "sk-RVApjtnPznKZ4UXosZYEOQ"
OPENAI_BASE_URL = "https://toknroutertybot.tybotflow.com/"

test_docs = [
    {
        "content": "Tyboo Studio est une plateforme avancée de création d'agents IA en drag-and-drop. Elle permet de connecter des LLM, des bases vectorielles comme Supabase et des mémoires Redis.",
        "metadata": {"source": "manual", "topic": "intro"}
    },
    {
        "content": "Le nœud Main RAG Agent est le cerveau du flux. Il récupère le contexte depuis Supabase avant d'envoyer la requête finale au Lite LLM (Tybot).",
        "metadata": {"source": "manual", "topic": "agent"}
    },
    {
        "content": "Pour configurer Redis dans Tyboo Studio, utilisez l'IP 192.168.100.59 et le port 6379 avec la base de données numéro 7.",
        "metadata": {"source": "config", "topic": "redis"}
    }
]

import uuid

async def seed():
    sb = create_client(SUPABASE_URL, SUPABASE_KEY)
    ai = OpenAI(api_key=OPENAI_API_KEY, base_url=OPENAI_BASE_URL)
    
    print("🚀 Ingestion des connaissances Tyboo...")
    
    for doc in test_docs:
        # Generate real embedding
        res = ai.embeddings.create(input=doc["content"], model="text-embedding-3-small")
        embedding = res.data[0].embedding
        
        # Insert into Supabase with explicit UUID
        data = {
            "id": str(uuid.uuid4()),
            "content": doc["content"],
            "metadata": doc["metadata"],
            "embedding": embedding
        }
        sb.table("documents").insert(data).execute()
        print(f"✅ Ajouté : {doc['content'][:40]}...")

if __name__ == "__main__":
    asyncio.run(seed())
