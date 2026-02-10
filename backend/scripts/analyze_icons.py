import json
import os

lib_path = "backend/data/node_library.json"

with open(lib_path, 'r', encoding='utf-8') as f:
    library = json.load(f)

total_nodes = 0
custom_icons = 0
lucide_icons = 0
missing_icons = []

for category, nodes in library.items():
    for node in nodes:
        total_nodes += 1
        icon = node.get('icon', '')
        if icon.startswith('/assets/icons/imported'):
            custom_icons += 1
        else:
            lucide_icons += 1
            missing_icons.append(f"{category} -> {node['name']} (Icon: {icon})")

print(f"Total Nodes: {total_nodes}")
print(f"Custom Icons: {custom_icons}")
print(f"Lucide Icons: {lucide_icons}")

if missing_icons:
    print("\nFirst 20 Missing Icons:")
    for m in missing_icons[:20]:
        print(f" - {m}")
