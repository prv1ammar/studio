import json
import os

def merge_libraries():
    data_dir = os.path.join("backend", "data")
    main_lib_path = os.path.join(data_dir, "node_library.json")
    migrated_lib_path = os.path.join(data_dir, "migrated_nodes.json")
    
    if not os.path.exists(main_lib_path):
        print(f"Error: {main_lib_path} not found.")
        return
    
    if not os.path.exists(migrated_lib_path):
        print(f"Error: {migrated_lib_path} not found.")
        return
        
    with open(main_lib_path, "r", encoding="utf-8") as f:
        main_lib = json.load(f)
        
    with open(migrated_lib_path, "r", encoding="utf-8") as f:
        migrated_lib = json.load(f)
        
    # 1. Add "Native Integrations" category if not exists
    if "Native Integrations" not in main_lib:
        main_lib["Native Integrations"] = []
    
    # Append nodes from migrated_nodes.json
    new_nodes = migrated_lib.get("Native Integrations", [])
    seen_ids = {n["id"] for n in main_lib["Native Integrations"]}
    
    added_count = 0
    for node in new_nodes:
        if node["id"] not in seen_ids:
            main_lib["Native Integrations"].append(node)
            seen_ids.add(node["id"])
            added_count += 1
            
    print(f"Added {added_count} new native nodes to 'Native Integrations' category.")

    # 2. Cleanup: Remove nodes with "composio" in their ID if they are redundant
    # Actually, the user wants them gone.
    cleaned_count = 0
    for cat in list(main_lib.keys()):
        original_len = len(main_lib[cat])
        main_lib[cat] = [n for n in main_lib[cat] if "composio" not in n["id"].lower()]
        cleaned_count += (original_len - len(main_lib[cat]))
        
    print(f"Removed {cleaned_count} legacy Composio nodes from library.")

    # 3. Save back
    with open(main_lib_path, "w", encoding="utf-8") as f:
        json.dump(main_lib, f, indent=2)
        
    print("Successfully updated node_library.json")

if __name__ == "__main__":
    merge_libraries()
