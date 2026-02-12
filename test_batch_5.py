import asyncio
import os
import sys
import json

# Setup path
project_root = os.path.abspath(os.path.dirname(__file__))
sys.path.append(os.path.join(project_root, "backend"))

from app.nodes.factory import NodeFactory

async def test_format_nodes():
    factory = NodeFactory()
    
    print("\n--- Testing text_formatter (uppercase) ---")
    node = factory.get_node("text_formatter", {"operation": "uppercase"})
    res = await node.run("hello studio", {})
    print(f"Result: {json.dumps(res, indent=2)}")
    
    print("\n--- Testing date_formatter ---")
    node = factory.get_node("date_formatter", {"output_format": "%A, %d %B %Y"})
    res = await node.run("2025-10-25", {"input_format": "%Y-%m-%d"}) # input_format in context or config
    # Actually DateFormatterNode takes input_format from config or defaults to ISO
    node = factory.get_node("date_formatter", {"output_format": "%A, %d %B %Y", "input_format": "%Y-%m-%d"})
    res = await node.run("2025-10-25", {})
    print(f"Result: {json.dumps(res, indent=2)}")

    print("\n--- Testing math_operation (multiply) ---")
    node = factory.get_node("math_operation", {"operation": "multiply", "value_b": 10})
    res = await node.run(5, {})
    print(f"Result: {json.dumps(res, indent=2)}")

if __name__ == "__main__":
    asyncio.run(test_format_nodes())
