import json
with open("backend/data/node_library.json", "r", encoding="utf-8") as f:
    data = json.load(f)
categories = set()
if isinstance(data, dict):
    # Keys are categories?
    categories.update(data.keys())
    # Also check internal category field if any
    for cat, nodes in data.items():
        if isinstance(nodes, list):
            for node in nodes:
                if isinstance(node, dict):
                    categories.add(node.get("category", cat))
elif isinstance(data, list):
     categories = {node.get("category", "Unknown") for node in data}

for cat in sorted(categories):
    print(cat)
