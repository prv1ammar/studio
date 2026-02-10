import json
import os

path = "backend/library_metadata.json"
with open(path, "r", encoding="utf-8") as f:
    library = json.load(f)

# Define Essentials
essentials = [
    {
        "id": "chatInput",
        "label": "Chat Input",
        "description": "Standard user message entry point.",
        "color": "#4f46e5",
        "icon": "MessageSquare",
        "inputs": [],
        "outputs": [{"name": "message", "type": "Text"}],
        "fields": [
            {"name": "input_value", "display_name": "Default Message", "_input_type": "MultilineInput"}
        ]
    },
    {
        "id": "chatOutput",
        "label": "Chat Output",
        "description": "Response display for the user.",
        "color": "#4f46e5",
        "icon": "LogOut",
        "inputs": [{"name": "message", "type": "Text"}],
        "outputs": [],
        "fields": []
    },
    {
        "id": "openaiModel",
        "label": "OpenAI Model",
        "description": "GPT series LLM connector.",
        "color": "#10a37f",
        "icon": "Cpu",
        "inputs": [{"name": "input", "type": "Text"}],
        "outputs": [{"name": "response", "type": "Text"}],
        "fields": [
            {"name": "model_name", "display_name": "Model", "_input_type": "DropdownInput", "options": ["gpt-4o", "gpt-4-turbo", "gpt-3.5-turbo"]},
            {"name": "api_key", "display_name": "API Key", "_input_type": "SecretStrInput", "required": True},
            {"name": "temperature", "display_name": "Temperature", "_input_type": "FloatInput", "value": 0.7}
        ]
    },
    {
        "id": "promptTemplate",
        "label": "Prompt Template",
        "description": "Format inputs into a structured prompt.",
        "color": "#f59e0b",
        "icon": "PenTool",
        "inputs": [{"name": "variables", "type": "Any"}],
        "outputs": [{"name": "prompt", "type": "Text"}],
        "fields": [
            {"name": "template", "display_name": "Template", "_input_type": "MultilineInput", "value": "Answer the following: {input}"}
        ]
    },
    {
        "id": "fileNode",
        "label": "File Extraction",
        "description": "Extract text from PDF, DOCX, or TXT files.",
        "color": "#6366f1",
        "icon": "FileText",
        "inputs": [],
        "outputs": [{"name": "text", "type": "Text"}],
        "fields": [
            {"name": "path", "display_name": "File Path", "_input_type": "StrInput", "info": "Local absolute path to the file."},
            {"name": "auto_table", "display_name": "Auto-Create Table", "_input_type": "BoolInput", "value": True, "info": "If true, creates a new table based on the filename."}
        ]
    }
]

# Define Tyboo Custom Nodes
tyboo_custom = [
    {
        "id": "mainAgent",
        "label": "Main RAG Agent",
        "description": "The 'Brain' node. Orchestrates tools and memory.",
        "color": "#3b82f6",
        "icon": "Bot",
        "inputs": [
            {"name": "input", "type": "Text"}, 
            {"name": "model", "type": "LanguageModel"},
            {"name": "memory", "type": "Memory"},
            {"name": "vectorstore", "type": "VectorStore"}
        ],
        "outputs": [{"name": "response", "type": "Text"}],
        "fields": [
            {"name": "system_prompt", "display_name": "Agent Instructions", "_input_type": "MultilineInput", "value": "You are a helpful assistant. Use the provided context to answer questions."},
            {"name": "tools", "display_name": "Available Tools", "_input_type": "DropdownInput", "options": ["WebSearch", "CRM_Lookup", "KnowledgeBase"], "value": "KnowledgeBase"}
        ]
    }, 
    {
        "id": "supabaseStore",
        "label": "Supabase Hybrid Store",
        "description": "High-speed vector storage for documents.",
        "color": "#10b981",
        "icon": "Database",
        "inputs": [{"name": "embedding", "type": "Vector"}],
        "outputs": [{"name": "vectorstore", "type": "VectorStore"}],
        "fields": [
            {"name": "table_name", "display_name": "Vector Table", "_input_type": "StrInput", "value": "documents"},
            {"name": "supabase_url", "display_name": "Supabase URL", "_input_type": "StrInput", "value": "https://xyz.supabase.co"},
            {"name": "api_key", "display_name": "Service Role Key", "_input_type": "SecretStrInput"}
        ]
    },
    {
        "id": "liteLLM",
        "label": "Lite LLM (Tybot)",
        "description": "Company-specific high-performance LLM.",
        "color": "#ec4899",
        "icon": "Cpu",
        "inputs": [{"name": "input", "type": "Text"}],
        "outputs": [{"name": "model", "type": "LanguageModel"}],
        "fields": [
            {"name": "api_key", "display_name": "LiteLLM API Key", "_input_type": "SecretStrInput", "value": "sk-RVApjtnPznKZ4UXosZYEOQ"},
            {"name": "base_url", "display_name": "Base URL", "_input_type": "StrInput", "value": "https://toknroutertybot.tybotflow.com/"},
            {"name": "model_name", "display_name": "Model Name", "_input_type": "StrInput", "value": "gpt-4.1-mini"},
            {"name": "temperature", "display_name": "Temperature", "_input_type": "FloatInput", "value": 0.1}
        ]
    },
    {
        "id": "liteEmbedding",
        "label": "Lite Embedding (Tybot)",
        "description": "Company-specific vector embedding model.",
        "color": "#8b5cf6",
        "icon": "Layers",
        "inputs": [{"name": "input", "type": "Text"}],
        "outputs": [{"name": "embeddings", "type": "Vector"}],
        "fields": [
            {"name": "api_key", "display_name": "LiteLLM API Key", "_input_type": "SecretStrInput", "value": "sk-RVApjtnPznKZ4UXosZYEOQ"},
            {"name": "base_url", "display_name": "Base URL", "_input_type": "StrInput", "value": "https://toknroutertybot.tybotflow.com/"},
            {"name": "model_name", "display_name": "Embedding Model", "_input_type": "StrInput", "value": "text-embedding-3-small"}
        ]
    }
]

# Remove collision keys from existing library to ensure injection works
if "Tyboo Custom" in library: del library["Tyboo Custom"]
if "Studio Essentials" in library: del library["Studio Essentials"]

# Create a new dictionary with Essentials and Tyboo Custom at the top
new_library = {
    "Tyboo Custom": tyboo_custom,
    "Studio Essentials": essentials
}
new_library.update(library)

with open(path, "w", encoding="utf-8") as f:
    json.dump(new_library, f, indent=2)

print("Injected Studio Essentials and Tyboo Custom into library_metadata.json")
