
import json
import os
from pathlib import Path

def extract_organization():
    index_path = r"C:\Users\info\Desktop\Nouveau dossier (2)\venv\Lib\site-packages\lfx\_assets\component_index.json"
    if not os.path.exists(index_path):
        print(f"Index not found at {index_path}")
        return

    with open(index_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    organization = {}
    
    # The structure is {"entries": [["Category", {"NodeName": { ... }}], ...]}
    for entry in data.get('entries', []):
        if not isinstance(entry, list) or len(entry) < 2:
            continue
            
        category = entry[0]
        nodes = entry[1]
        
        if not isinstance(nodes, dict):
            continue
            
        if category not in organization:
            organization[category] = []
            
        for node_name, node_data in nodes.items():
            # In some cases, node_data is another dict with the actual data
            if node_name in node_data and isinstance(node_data[node_name], dict):
                node_data = node_data[node_name]
                
            node_info = {
                "name": node_name,
                "display_name": node_data.get("display_name", node_name),
                "description": node_data.get("description", ""),
                "icon": node_data.get("icon", ""),
                "beta": node_data.get("beta", False),
                "legacy": node_data.get("legacy", False)
            }
            organization[category].append(node_info)

    # Sort categories and nodes
    sorted_org = {}
    for cat in sorted(organization.keys()):
        sorted_org[cat] = sorted(organization[cat], key=lambda x: x['display_name'])

    with open("langflow_organization.json", "w", encoding='utf-8') as f:
        json.dump(sorted_org, f, indent=2)

    # Create a markdown summary
    with open("langflow_nodes_summary.md", "w", encoding='utf-8') as f:
        f.write("# Langflow Nodes Organization\n\n")
        for cat, nodes in sorted_org.items():
            f.write(f"## {cat}\n")
            for node in nodes:
                status = ""
                if node['beta']: status += " (Beta)"
                if node['legacy']: status += " (Legacy)"
                f.write(f"- **{node['display_name']}**{status}: {node['description']} (Icon: {node['icon']})\n")
            f.write("\n")

    print(f"Extracted {len(sorted_org)} categories and saved to langflow_organization.json and langflow_nodes_summary.md")

if __name__ == "__main__":
    extract_organization()
