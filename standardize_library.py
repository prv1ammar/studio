import json
import os

LIBRARY_PATH = "backend/data/node_library.json"

CATEGORY_MAPPING = {
    # Models
    "Amazon": "Models & AI Providers",
    "Anthropic": "Models & AI Providers",
    "Azure": "Models & AI Providers",
    "Baidu": "Models & AI Providers",
    "Bing": "Models & AI Providers",
    "Cohere": "Models & AI Providers",
    "Deepseek": "Models & AI Providers",
    "Google": "Models & AI Providers",
    "Groq": "Models & AI Providers",
    "Huggingface": "Models & AI Providers",
    "Ibm": "Models & AI Providers",
    "Lmstudio": "Models & AI Providers",
    "Mistral": "Models & AI Providers",
    "Novita": "Models & AI Providers",
    "Nvidia": "Models & AI Providers",
    "Ollama": "Models & AI Providers",
    "Openai": "Models & AI Providers",
    "Openrouter": "Models & AI Providers",
    "Perplexity": "Models & AI Providers",
    "Sambanova": "Models & AI Providers",
    "Vertexai": "Models & AI Providers",
    "Vlmrun": "Models & AI Providers",
    "Xai": "Models & AI Providers",
    "Embeddings": "Models & AI Providers",
    "Llm_Operations": "Models & AI Providers",

    # Vector Stores & DBs
    "Cassandra": "Vector Stores & Databases",
    "Chroma": "Vector Stores & Databases",
    "Cleanlab": "Vector Stores & Databases",
    "Clickhouse": "Vector Stores & Databases",
    "Couchbase": "Vector Stores & Databases",
    "Datastax": "Vector Stores & Databases",
    "Elastic": "Vector Stores & Databases",
    "Faiss": "Vector Stores & Databases",
    "Milvus": "Vector Stores & Databases",
    "Mongodb": "Vector Stores & Databases",
    "Pgvector": "Vector Stores & Databases",
    "Pinecone": "Vector Stores & Databases",
    "Qdrant": "Vector Stores & Databases",
    "Redis": "Vector Stores & Databases",
    "Supabase": "Vector Stores & Databases",
    "Upstash": "Vector Stores & Databases",
    "Vectara": "Vector Stores & Databases",
    "Vectorstores": "Vector Stores & Databases",
    "Weaviate": "Vector Stores & Databases",
    "Zep": "Vector Stores & Databases",

    # Agents
    "Agents": "AI Services & Agents",
    "Crewai": "AI Services & Agents",
    "Models_And_Agents": "AI Services & Agents",
    "Essentials": "AI Services & Agents",
    "Automations": "AI Services & Agents",

    # Tools & Utils
    "Langchain_Utilities": "Tools & Utilities",
    "Utilities": "Tools & Utilities",
    "Tools": "Tools & Utilities",
    "Cometapi": "Tools & Utilities",
    "Composio": "Tools & Utilities",
    "Custom_Component": "Custom Components",
    "Tools & Analytics": "Tools & Analytics",

    # Data
    "Data_Source": "Data Sources",
    "Files_And_Knowledge": "Data & Knowledge",
    "Input_Output": "Input / Output",
    "Processing": "Data Processing",

    # Search & Scraping
    "Agentql": "Search & Scraping",
    "Apify": "Search & Scraping",
    "Arxiv": "Search & Scraping",
    "Duckduckgo": "Search & Scraping",
    "Exa": "Search & Scraping",
    "Firecrawl": "Search & Scraping",
    "Glean": "Search & Scraping",
    "Google": "Search & Scraping",  # Might overlap with Models, check content?
    "Scrapegraph": "Search & Scraping",
    "Searchapi": "Search & Scraping",
    "Serpapi": "Search & Scraping",
    "Tavily": "Search & Scraping",
    "Wikipedia": "Search & Scraping",
    "Yahoosearch": "Search & Scraping",
    "Youtube": "Search & Scraping",
    "Altk": "Search & Scraping",

    # Core
    "Flow_Controls": "Logic & Flow",
    "Git": "Dev Tools",
    "Automation & Dev": "Dev Tools",
    "Homeassistant": "IoT & Home",
    "Notion": "Productivity",
    "Confluence": "Productivity",
    "Jigsawstack": "Productivity",
    "Maritalk": "Productivity",
    "Mem0": "Memory",
    "Needle": "Memory",
    "Notdiamond": "Models & AI Providers", # Routing model
    "Olivya": "AI Services & Agents",
    "Unstructured": "Data Processing",
    "Docling": "Data Processing"
}

def standardize():
    if not os.path.exists(LIBRARY_PATH):
        print("Library file not found")
        return

    with open(LIBRARY_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    new_data = {}
    
    # Initialize some categories to ensure order if desired
    # ...

    for category, nodes in data.items():
        # Determine new category name
        new_cat = CATEGORY_MAPPING.get(category, category)
        
        # Normalize Title Case for unmapped ones
        if new_cat == category and "_" in category:
             new_cat = category.replace("_", " ").title()

        if new_cat not in new_data:
            new_data[new_cat] = []
        
        # Update node objects
        for node in nodes:
            node["category"] = new_cat
            # Ensure label is nice?
            if "label" in node:
                # remove emojis?
                pass
            new_data[new_cat].append(node)

    # Sort categories alphabetically
    sorted_data = dict(sorted(new_data.items()))

    with open(LIBRARY_PATH, "w", encoding="utf-8") as f:
        json.dump(sorted_data, f, indent=2)
    
    print(f"Standardized {len(data)} categories into {len(sorted_data)} categories.")

if __name__ == "__main__":
    standardize()
