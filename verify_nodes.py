import asyncio
import sys
import os

# Add backend to sys.path
sys.path.append(os.path.abspath("backend"))

from app.nodes.registry import NodeRegistry

async def main():
    print("Starting Node Scan...")
    nodes = NodeRegistry.get_all_nodes()
    print(f"SUCCESS: Total Nodes Registered: {len(nodes)}")
    
    # Print some examples
    node_ids = list(nodes.keys())
    print(f"Sample Nodes: {', '.join(node_ids[:20])}...")

if __name__ == "__main__":
    asyncio.run(main())
