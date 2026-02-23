import sys
import os
import json

# Add backend to path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.append(os.path.join(project_root, "backend"))

from app.nodes.registry import NodeRegistry
from app.nodes.factory import NODE_MAP

def check_nodes():
    print("--- SCANNING REGISTRY ---")
    nodes = NodeRegistry.get_all_nodes()
    print(f"Total nodes in registry: {len(nodes)}")
    
    search_nodes = ["slack_node", "slack_action", "slack_message_send", "gmail_send", "notion_node"]
    
    for sn in search_nodes:
        cls = nodes.get(sn)
        if cls:
            print(f"✅ FOUND in Registry: {sn} -> {cls.__module__}.{cls.__name__}")
        else:
            print(f"❌ MISSING from Registry: {sn}")
            
    print("\n--- CHECKING NODE_MAP ---")
    for sn in search_nodes:
        mapped = NODE_MAP.get(sn)
        if mapped:
            print(f"📍 NODE_MAP: {sn} -> {mapped}")
        else:
            print(f"⚠️  NODE_MAP: {sn} is NOT in NODE_MAP")

    print("\n--- CHECKING library.json ---")
    lib_path = os.path.join(project_root, "backend", "data", "node_library.json")
    if os.path.exists(lib_path):
        with open(lib_path, "r", encoding="utf-8") as f:
            lib = json.load(f)
        
        found_in_lib = []
        for cat, components in lib.items():
            for comp in components:
                if any(sn == comp["id"] for sn in search_nodes):
                    found_in_lib.append(f"{comp['id']} (Category: {cat})")
        
        if found_in_lib:
            print(f"✅ Found in library.json: {', '.join(found_in_lib)}")
        else:
            print("❌ None of the searched nodes found in library.json")
    else:
        print("❌ library.json NOT FOUND")

if __name__ == "__main__":
    check_nodes()
