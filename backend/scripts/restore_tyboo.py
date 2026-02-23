import json
import os

LIB_PATH = 'backend/data/node_library.json'

TYBOO_NODES = [
    {
        "id": "liteLLM",
        "name": "LiteLLM",
        "label": "Lite LLM (Tybot)",
        "description": "High-performance company-specific LLM router.",
        "category": "Tyboo",
        "icon": "Cpu",
        "color": "#ec4899",
        "inputs": [
            {"name": "input_data", "display_name": "Input Text", "type": "handle", "required": True},
            {"name": "api_key", "display_name": "API Key", "type": "password", "required": True, "default": "sk-RVApjtnPznKZ4UXosZYEOQ"},
            {"name": "base_url", "display_name": "Base URL", "type": "text", "default": "https://toknroutertybot.tybotflow.com/"},
            {"name": "model_name", "display_name": "Model Name", "type": "text", "default": "gpt-4.1-mini"},
            {"name": "temperature", "display_name": "Temperature", "type": "number", "default": 0.1}
        ],
        "outputs": [{"name": "response", "display_name": "Assistant Response", "types": ["Text"]}]
    },
    {
        "id": "langchainAgent",
        "name": "LangChainAgent",
        "label": "Configurable Agent (LangChain)",
        "description": "Powerful agent that composes LLM, Tools, and Memory from its inputs.",
        "category": "Tyboo",
        "icon": "Zap",
        "color": "#f59e0b",
        "inputs": [
            {"name": "input_data", "display_name": "User Question", "type": "handle", "required": True},
            {"name": "system_prompt", "display_name": "System Prompt", "type": "textarea", "default": "You are a helpful assistant."},
            {"name": "llm", "display_name": "LLM Provider", "type": "handle", "info": "Connect an LLM node (e.g., LiteLLM)."},
            {"name": "tools", "display_name": "Tools", "type": "handle", "info": "Connect Tool nodes (e.g., SmartDB)."},
        ],
        "outputs": [{"name": "output", "display_name": "Agent Response", "types": ["Text"]}]
    },
    {
        "id": "liteEmbedding",
        "name": "LiteEmbedding",
        "label": "Tyboo Embedding",
        "description": "Proprietary vector embedding model for semantic search.",
        "category": "Tyboo",
        "icon": "Layers",
        "color": "#8b5cf6",
        "inputs": [
            {"name": "input_data", "display_name": "Text to Embed", "type": "handle", "required": True},
            {"name": "api_key", "display_name": "API Key", "type": "password", "required": True, "default": "sk-RVApjtnPznKZ4UXosZYEOQ"},
            {"name": "base_url", "display_name": "Base URL", "type": "text", "default": "https://toknroutertybot.tybotflow.com/"},
            {"name": "model_name", "display_name": "Embedding Model", "type": "text", "default": "text-embedding-3-small"}
        ],
        "outputs": [{"name": "embeddings", "display_name": "Vector Embeddings", "types": ["Vector"]}]
    },
    {
        "id": "smartDB",
        "name": "SmartDB",
        "label": "SmartDB (NocoDB)",
        "description": "Connect to your NocoDB instance with automated schema discovery.",
        "category": "Tyboo",
        "icon": "Database",
        "color": "#10b981",
        "inputs": [
            {"name": "input_data", "display_name": "Operation Data", "type": "handle", "required": False},
            {"name": "base_url", "display_name": "NocoDB URL", "type": "text", "default": "https://nocodb.tybot.ma"},
            {"name": "api_key", "display_name": "API Key", "type": "password", "default": "s-m7Ue3MzAsf7AuNrzYyhL0Oz5NQoyEuT18vcI7X"},
            {"name": "project_id", "display_name": "Select Database", "type": "dropdown", "options": []},
            {"name": "table_id", "display_name": "Select Table", "type": "dropdown", "options": []},
            {"name": "operations", "display_name": "Operations", "type": "dropdown", "options": ["Create", "Read", "Update", "Delete", "All"]}
        ],
        "outputs": [{"name": "result", "display_name": "Query Result", "types": ["Any"]}]
    }
]

def restore_tyboo():
    if not os.path.exists(LIB_PATH):
        print("Error: node_library.json not found.")
        return

    with open(LIB_PATH, 'r', encoding='utf-8') as f:
        library = json.load(f)

    # 1. Ensure Tyboo category exists at the top
    # Reconstruct library to maintain order (Tyboo first is often preferred by user)
    new_library = {"Tyboo": TYBOO_NODES}
    
    for cat, nodes in library.items():
        if cat != "Tyboo":
            new_library[cat] = nodes

    # 2. Save
    with open(LIB_PATH, 'w', encoding='utf-8') as f:
        json.dump(new_library, f, indent=2)

    print("Successfully restored 'Tyboo' category with 4 core nodes.")

if __name__ == '__main__':
    restore_tyboo()
