import json
import sys

# Load the node library
with open('backend/data/node_library.json', 'r', encoding='utf-8') as f:
    lib = json.load(f)

print("=== FIXING NODE LIBRARY ===\n")

# 1. Remove duplicate langchainAgent (keep the one with 5 inputs)
tyboo_nodes = lib.get('Tyboo', [])
print(f"Original Tyboo nodes: {len(tyboo_nodes)}")

# Find indices of langchainAgent
langchain_indices = [i for i, n in enumerate(tyboo_nodes) if n.get('id') == 'langchainAgent']
print(f"Found langchainAgent at indices: {langchain_indices}")

if len(langchain_indices) > 1:
    # Keep the one with more inputs (index 1), remove the other (index 4)
    print(f"Removing duplicate at index {langchain_indices[1]}")
    tyboo_nodes.pop(langchain_indices[1])
    lib['Tyboo'] = tyboo_nodes
    print(f"New Tyboo nodes count: {len(tyboo_nodes)}")

# 2. Update the remaining langchainAgent to have proper Universal Agent configuration
for i, node in enumerate(tyboo_nodes):
    if node.get('id') == 'langchainAgent':
        print(f"\nUpdating langchainAgent at index {i}...")
        
        # Update metadata
        node['label'] = 'Universal Agent'
        node['description'] = 'Dynamic LangChain agent with three orchestration tiers: Simple (LCEL), Standard (Tool-Calling), and Planner (ReAct). Automatically discovers LLM, Tools, Memory, and Prompts from connected nodes.'
        
        # Define proper inputs
        node['inputs'] = [
            {
                "name": "input_data",
                "display_name": "User Input",
                "type": "handle",
                "required": True,
                "description": "The user's message or query",
                "types": ["Text", "Message"]
            },
            {
                "name": "llm",
                "display_name": "LLM",
                "type": "handle",
                "required": False,
                "description": "Connect an LLM node (LiteLLM, OpenAI, etc.)",
                "types": ["LLM"]
            },
            {
                "name": "tools",
                "display_name": "Tools",
                "type": "handle",
                "required": False,
                "description": "Connect tool nodes (SmartDB, Supabase, etc.)",
                "types": ["Tool"]
            },
            {
                "name": "memory",
                "display_name": "Memory",
                "type": "handle",
                "required": False,
                "description": "Connect a memory node for conversation history",
                "types": ["Memory"]
            },
            {
                "name": "system_prompt",
                "display_name": "System Prompt",
                "type": "textarea",
                "required": False,
                "description": "Custom instructions for the agent",
                "default": "You are a helpful AI assistant.",
                "advanced": True
            },
            {
                "name": "agent_pattern",
                "display_name": "Agent Pattern",
                "type": "dropdown",
                "required": False,
                "description": "Choose the orchestration pattern",
                "default": "standard",
                "options": ["simple", "standard", "planner"],
                "advanced": True
            }
        ]
        
        # Define proper outputs
        node['outputs'] = [
            {
                "name": "output",
                "display_name": "Agent Response",
                "types": ["Text", "Message"]
            }
        ]
        
        print("[OK] Updated langchainAgent configuration")

# 3. Add a dedicated UniversalAgent entry (for clarity)
universal_agent_node = {
    "id": "universalAgent",
    "name": "UniversalAgent",
    "label": "Universal Agent",
    "description": "Next-generation agent with automatic tier selection (Simple/Standard/Planner) based on task complexity.",
    "category": "Tyboo",
    "icon": "Zap",
    "color": "#8b5cf6",
    "inputs": [
        {
            "name": "input_data",
            "display_name": "User Input",
            "type": "handle",
            "required": True,
            "description": "The user's message or query",
            "types": ["Text", "Message"]
        },
        {
            "name": "llm",
            "display_name": "LLM",
            "type": "handle",
            "required": False,
            "description": "Connect an LLM node",
            "types": ["LLM"]
        },
        {
            "name": "tools",
            "display_name": "Tools",
            "type": "handle",
            "required": False,
            "description": "Connect tool nodes",
            "types": ["Tool"]
        },
        {
            "name": "memory",
            "display_name": "Memory",
            "type": "handle",
            "required": False,
            "description": "Connect a memory node",
            "types": ["Memory"]
        },
        {
            "name": "system_prompt",
            "display_name": "System Prompt",
            "type": "textarea",
            "required": False,
            "description": "Custom instructions",
            "default": "You are a helpful AI assistant.",
            "advanced": True
        },
        {
            "name": "agent_pattern",
            "display_name": "Agent Pattern",
            "type": "dropdown",
            "required": False,
            "description": "Orchestration tier: simple (LCEL), standard (Tool-Calling), planner (ReAct)",
            "default": "standard",
            "options": ["simple", "standard", "planner"],
            "advanced": True
        }
    ],
    "outputs": [
        {
            "name": "output",
            "display_name": "Agent Response",
            "types": ["Text", "Message"]
        }
    ],
    "base_classes": ["Agent"],
    "beta": False,
    "documentation": ""
}

# Check if universalAgent already exists
if not any(n.get('id') == 'universalAgent' for n in tyboo_nodes):
    print("\nAdding universalAgent node...")
    tyboo_nodes.append(universal_agent_node)
    lib['Tyboo'] = tyboo_nodes
    print("[OK] Added universalAgent")
else:
    print("\nuniversalAgent already exists, updating it...")
    for i, node in enumerate(tyboo_nodes):
        if node.get('id') == 'universalAgent':
            tyboo_nodes[i] = universal_agent_node
            lib['Tyboo'] = tyboo_nodes
            print("[OK] Updated universalAgent")

# Save the updated library
with open('backend/data/node_library.json', 'w', encoding='utf-8') as f:
    json.dump(lib, f, indent=2, ensure_ascii=False)

print("\n=== COMPLETE ===")
print(f"Final Tyboo nodes count: {len(lib['Tyboo'])}")
