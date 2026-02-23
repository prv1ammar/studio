import json
import os

LIB_PATH = 'backend/data/node_library.json'

AGENT_NODES = [
    {
        "id": "react_agent_node",
        "name": "ReActAgent",
        "label": "ReAct Agent",
        "description": "Think -> Act -> Observe reasoning loop. Best for complex multi-step tasks requiring tools.",
        "category": "Agents",
        "icon": "Zap",
        "color": "#f59e0b",
        "inputs": [
            {"name": "input_data", "display_name": "Task/Question", "type": "handle", "required": True},
            {"name": "system_prompt", "display_name": "System Instructions", "type": "textarea", "default": "You are a helpful assistant. Answer the user question as best as you can. You have access to tools."},
            {"name": "llm", "display_name": "Connect Model", "type": "handle", "info": "Connect an LLM node (e.g. LiteLLM, OpenAI)."},
            {"name": "tools", "display_name": "Connect Tools", "type": "handle", "info": "Connect one or more tool nodes."}
        ],
        "outputs": [{"name": "text", "display_name": "Final Answer", "types": ["Text"]}, {"name": "intermediate_steps", "display_name": "Reasoning Steps", "types": ["List"]}]
    },
    {
        "id": "conversational_agent_node",
        "name": "ConversationalAgent",
        "label": "Conversational Agent",
        "description": "Chat-optimized agent with memory support. Best for interactive bots and long conversations.",
        "category": "Agents",
        "icon": "MessageCircle",
        "color": "#3b82f6",
        "inputs": [
            {"name": "input_data", "display_name": "User Message", "type": "handle", "required": True},
            {"name": "llm", "display_name": "Connect Model", "type": "handle"},
            {"name": "chat_history", "display_name": "Connect Memory", "type": "handle"},
            {"name": "system_prompt", "display_name": "Bot Persona", "type": "textarea", "default": "You are a warm and helpful AI assistant."}
        ],
        "outputs": [{"name": "text", "display_name": "Response", "types": ["Text"]}]
    },
    {
        "id": "tool_calling_agent_node",
        "name": "ToolCallingAgent",
        "label": "Tool-Calling Agent",
        "description": "Uses native tool-calling capabilities. Faster and more reliable for modern models (GPT-4, Claude).",
        "category": "Agents",
        "icon": "Wrench",
        "color": "#10b981",
        "inputs": [
            {"name": "input_data", "display_name": "Input", "type": "handle", "required": True},
            {"name": "llm", "display_name": "Connect Model", "type": "handle"},
            {"name": "tools", "display_name": "Connect Tools", "type": "handle"},
            {"name": "system_prompt", "display_name": "Instructions", "type": "textarea", "default": "You are a task-oriented assistant."}
        ],
        "outputs": [{"name": "text", "display_name": "Output", "types": ["Text"]}]
    },
    {
        "id": "plan_execute_agent_node",
        "name": "PlanExecuteAgent",
        "label": "Plan & Execute Agent",
        "description": "Advanced reasoning: Creates a multi-step plan first, then executes it. Best for very complex goals.",
        "category": "Agents",
        "icon": "ListChecks",
        "color": "#8b5cf6",
        "inputs": [
            {"name": "input_data", "display_name": "Complex Goal", "type": "handle", "required": True},
            {"name": "llm", "display_name": "Connect Model", "type": "handle"},
            {"name": "tools", "display_name": "Connect Tools", "type": "handle"}
        ],
        "outputs": [{"name": "text", "display_name": "Final Result", "types": ["Text"]}, {"name": "plan", "display_name": "Generated Plan", "types": ["Text"]}]
    },
    {
        "id": "openai_functions_agent_node",
        "name": "OpenAIFunctionsAgent",
        "label": "OpenAI Functions Agent",
        "description": "Uses legacy OpenAI Functions API. Use for older GPT models.",
        "category": "Agents",
        "icon": "Cpu",
        "color": "#0ea5e9",
        "inputs": [
            {"name": "input_data", "display_name": "Input", "type": "handle", "required": True},
            {"name": "llm", "display_name": "Connect Model", "type": "handle"}
        ],
        "outputs": [{"name": "text", "display_name": "Output", "types": ["Text"]}]
    },
    {
        "id": "sql_agent_node",
        "name": "SQLAgent",
        "label": "SQL Agent",
        "description": "Talk to your database in plain English. Generates and runs SQL queries safely.",
        "category": "Agents",
        "icon": "Database",
        "color": "#f43f5e",
        "inputs": [
            {"name": "input_data", "display_name": "Natural Language Question", "type": "handle", "required": True},
            {"name": "connection_string", "display_name": "DB Connection URI", "type": "text", "placeholder": "postgresql://user:pass@host/db"},
            {"name": "llm", "display_name": "Connect Model", "type": "handle"}
        ],
        "outputs": [{"name": "text", "display_name": "Answer", "types": ["Text"]}]
    }
]

def inject_agents():
    if not os.path.exists(LIB_PATH):
        print("Error: node_library.json not found.")
        return

    with open(LIB_PATH, 'r', encoding='utf-8') as f:
        library = json.load(f)

    # 1. Add 'Agents' category after 'Tyboo' and 'Native Integrations'
    new_library = {}
    
    # Priority order
    order = ["Tyboo", "Native Integrations", "Agents"]
    
    for cat in order:
        if cat == "Agents":
            new_library["Agents"] = AGENT_NODES
        elif cat in library:
            new_library[cat] = library[cat]

    # Add remaining categories
    for cat, nodes in library.items():
        if cat not in new_library:
            new_library[cat] = nodes

    # 2. Save
    with open(LIB_PATH, 'w', encoding='utf-8') as f:
        json.dump(new_library, f, indent=2)

    print(f"Successfully injected {len(AGENT_NODES)} LangChain-powered Agent nodes into the library.")

if __name__ == '__main__':
    inject_agents()
