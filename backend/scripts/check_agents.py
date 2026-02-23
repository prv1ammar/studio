import json

with open('backend/data/node_library.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

print("--- AI Services & Agents Nodes ---")
for node in data.get('AI Services & Agents', []):
    print(f"ID: {node.get('id')} | Name: {node.get('name')} | Desc: {node.get('description')}")

print("\n--- Tyboo Nodes ---")
for node in data.get('Tyboo', []):
    print(f"ID: {node.get('id')} | Name: {node.get('name')} | Desc: {node.get('description')}")
