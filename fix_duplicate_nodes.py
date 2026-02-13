import json

LIBRARY_PATH = "backend/data/node_library.json"

def fix_duplicates():
    """Remove duplicate finance nodes from Productivity category."""
    with open(LIBRARY_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    # IDs to remove from Productivity
    duplicate_ids = ["quickbooks_node", "paypal_node", "stripe_node"]
    
    # Remove from Productivity category
    if "Productivity" in data:
        original_count = len(data["Productivity"])
        data["Productivity"] = [
            node for node in data["Productivity"] 
            if node.get("id") not in duplicate_ids
        ]
        removed = original_count - len(data["Productivity"])
        print(f"Removed {removed} duplicate nodes from Productivity category")
    
    # Verify they exist in Finance
    if "Finance" in data:
        finance_ids = [node.get("id") for node in data["Finance"]]
        for dup_id in duplicate_ids:
            if dup_id in finance_ids:
                print(f"✓ {dup_id} exists in Finance category")
            else:
                print(f"✗ WARNING: {dup_id} NOT found in Finance category!")
    
    # Save the cleaned library
    with open(LIBRARY_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    
    print(f"\n✅ Fixed duplicate nodes. Library saved.")

if __name__ == "__main__":
    fix_duplicates()
