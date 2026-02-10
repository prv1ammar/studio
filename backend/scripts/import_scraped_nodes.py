"""
Script to import scraped nodes from component_index.json into the Studio backend.
This will process all nodes and create the necessary backend structure.
"""

import json
import os
from pathlib import Path
from typing import Dict, List, Any

# Paths
SCRAPED_INDEX = r"c:\Users\PC\Pictures\scrapung_studio\Node System\component_index.json"
BACKEND_DIR = r"c:\Users\PC\Pictures\studio_tyboo-main\backend"
OUTPUT_FILE = os.path.join(BACKEND_DIR, "data", "imported_nodes.json")

def load_component_index() -> Dict:
    """Load the scraped component index."""
    print(f"Loading component index from: {SCRAPED_INDEX}")
    with open(SCRAPED_INDEX, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return data

def extract_node_metadata(component_data: Dict) -> Dict:
    """Extract essential metadata from a component."""
    return {
        "display_name": component_data.get("display_name", "Unknown"),
        "description": component_data.get("description", ""),
        "icon": component_data.get("icon", "Box"),
        "category": component_data.get("metadata", {}).get("module", "").split(".")[2] if "metadata" in component_data else "Other",
        "base_classes": component_data.get("base_classes", []),
        "inputs": [
            {
                "name": inp.get("name"),
                "display_name": inp.get("display_name", inp.get("name")),
                "type": inp.get("type", "str"),
                "required": inp.get("required", False),
                "info": inp.get("info", "")
            }
            for inp_name, inp in component_data.get("template", {}).items()
            if isinstance(inp, dict) and inp.get("show", True) and inp_name != "code" and inp_name != "_type"
        ],
        "outputs": [
            {
                "name": out.get("name"),
                "display_name": out.get("display_name"),
                "types": out.get("types", [])
            }
            for out in component_data.get("outputs", [])
        ]
    }

def process_all_nodes(index_data: Dict) -> Dict[str, List[Dict]]:
    """Process all nodes and organize by category."""
    categorized_nodes = {}
    total_nodes = 0
    
    for category_name, category_data in index_data.get("entries", []):
        print(f"\nProcessing category: {category_name}")
        category_nodes = []
        
        for node_name, node_data in category_data.items():
            try:
                metadata = extract_node_metadata(node_data)
                metadata["id"] = f"{category_name}_{node_name}"
                metadata["original_name"] = node_name
                category_nodes.append(metadata)
                total_nodes += 1
            except Exception as e:
                print(f"  ⚠️  Error processing {node_name}: {e}")
        
        if category_nodes:
            categorized_nodes[category_name] = category_nodes
            print(f"  ✓ Processed {len(category_nodes)} nodes")
    
    print(f"\n✅ Total nodes processed: {total_nodes}")
    print(f"✅ Total categories: {len(categorized_nodes)}")
    
    return categorized_nodes

def save_processed_nodes(nodes: Dict[str, List[Dict]]):
    """Save processed nodes to output file."""
    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
    
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(nodes, f, indent=2, ensure_ascii=False)
    
    print(f"\n💾 Saved processed nodes to: {OUTPUT_FILE}")

def generate_category_summary(nodes: Dict[str, List[Dict]]) -> str:
    """Generate a summary of all categories."""
    summary = "\n" + "="*60 + "\n"
    summary += "IMPORTED NODES SUMMARY\n"
    summary += "="*60 + "\n\n"
    
    for category, node_list in sorted(nodes.items()):
        summary += f"{category}: {len(node_list)} nodes\n"
        for node in node_list[:3]:  # Show first 3 nodes
            summary += f"  - {node['display_name']}\n"
        if len(node_list) > 3:
            summary += f"  ... and {len(node_list) - 3} more\n"
        summary += "\n"
    
    return summary

def main():
    print("="*60)
    print("SCRAPED NODES IMPORT SCRIPT")
    print("="*60)
    
    # Load index
    index_data = load_component_index()
    
    # Process nodes
    categorized_nodes = process_all_nodes(index_data)
    
    # Save results
    save_processed_nodes(categorized_nodes)
    
    # Print summary
    summary = generate_category_summary(categorized_nodes)
    print(summary)
    
    # Save summary
    summary_file = os.path.join(BACKEND_DIR, "data", "import_summary.txt")
    with open(summary_file, 'w', encoding='utf-8') as f:
        f.write(summary)
    print(f"📄 Summary saved to: {summary_file}")

if __name__ == "__main__":
    main()
