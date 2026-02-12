import asyncio
import os
import sys
import json

# Setup path
project_root = os.path.abspath(os.path.dirname(__file__))
sys.path.append(os.path.join(project_root, "backend"))

from app.nodes.factory import NodeFactory

async def test_json_nodes():
    factory = NodeFactory()
    
    print("\n--- Testing json_query ---")
    query_node = factory.get_node("json_query", {"query": ".items[0].name"})
    input_data = {"items": [{"name": "Alice"}, {"name": "Bob"}]}
    res = await query_node.run(input_data, {})
    print(f"Result: {json.dumps(res, indent=2)}")
    
    print("\n--- Testing json_transform (rename) ---")
    transform_node = factory.get_node("json_transform", {"operation": "rename", "keys": {"old": "new"}})
    res = await transform_node.run({"old": 123, "other": 456}, {})
    print(f"Result: {json.dumps(res, indent=2)}")

    print("\n--- Testing json_parse ---")
    parse_node = factory.get_node("json_parse", {"repair": True})
    res = await parse_node.run('{"broken": "json", }', {})
    print(f"Result: {json.dumps(res, indent=2)}")

if __name__ == "__main__":
    asyncio.run(test_json_nodes())
