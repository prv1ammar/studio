import sys
import os
import asyncio

# Setup paths
project_root = os.path.abspath(os.path.dirname(__file__))
sys.path.append(project_root)
sys.path.append(os.path.join(project_root, "backend"))

from app.nodes.registry import NodeRegistry

def test_registry():
    print("Starting NodeRegistry Test...")
    NodeRegistry.scan_and_register()
    nodes = NodeRegistry.get_all_nodes()
    
    print(f"Total Registered Nodes: {len(nodes)}")
    print("Registered IDs:", sorted(list(nodes.keys())))
    
    # Check for core nodes
    core_check = ["chatInput", "chatOutput", "memoryNode", "liteLLM", "langchainAgent"]
    for nid in core_check:
        status = "OK" if nid in nodes else "MISSING"
        print(f"  {status} Core: {nid}")
        
    # Check for Ghost nodes mapped to Universal API
    ghost_check = ["hubspotNode", "salesforceNode", "sageNode"]
    for nid in ghost_check:
        status = "OK" if nid in nodes else "MISSING"
        node_class = nodes.get(nid)
        class_name = node_class.__name__ if node_class else "None"
        print(f"  {status} Ghost: {nid} -> {class_name}")

if __name__ == "__main__":
    test_registry()
