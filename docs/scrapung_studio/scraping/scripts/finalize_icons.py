
import json
import os
import shutil
import re

def to_kebab_case(name):
    namelist = []
    # separate by uppercase
    # e.g. MessageSquare -> Message Square -> message-square
    # But be careful with abbreviations or already kebab strings
    
    # Simple regex to insert space before caps
    s1 = re.sub('(.)([A-Z][a-z]+)', r'\1-\2', name)
    return re.sub('([a-z0-9])([A-Z])', r'\1-\2', s1).lower()

def normalize_filename(filename):
    # Remove extension
    base = os.path.splitext(filename)[0]
    # Remove hash suffix if present (usually -[A-Za-z0-9_]{8})
    # The files look like "activity-ZVJc3e7F.svg"
    # We want "activity"
    
    # Check if there's a hyphen followed by a "hash-like" string at the end
    # Or just split by last hyphen?
    # Some icons might have multiple hyphens: "align-center-horizontal-B5o6iphB"
    
    parts = base.rsplit('-', 1)
    if len(parts) == 2:
        # We assume the last part is a hash if it looks like one, or we just take the prefix
        # Given the format "name-HASH", taking everything before the last dash is generally safe 
        # for these assets unless the icon name itself ends in a dash (unlikely)
        return parts[0].lower()
    return base.lower()

def finalize_structure():
    base_dir = r"C:\Users\info\Desktop\Nouveau dossier (2)\langflow_icons"
    org_file = r"C:\Users\info\Desktop\Nouveau dossier (2)\langflow_organization.json"
    output_dir = os.path.join(base_dir, "Final-Structure")
    
    if os.path.exists(output_dir):
        shutil.rmtree(output_dir)
    os.makedirs(output_dir, exist_ok=True)

    # 1. Index available icons
    icon_map = {} # normalized_name -> path
    
    search_dirs = [
        os.path.join(base_dir, "Lucide-Library"),
        os.path.join(base_dir, "Brand-Icons"),
        # Also check extracted root just in case
        os.path.join(base_dir, "extracted") 
    ]
    
    print("Indexing icons...")
    for search_dir in search_dirs:
        if not os.path.exists(search_dir):
            continue
        for root, dirs, files in os.walk(search_dir):
            for file in files:
                if file.endswith(".svg"):
                    full_path = os.path.join(root, file)
                    normalized = normalize_filename(file)
                    icon_map[normalized] = full_path
                    # Also map the literal filename (lowercased) just in case
                    icon_map[file.lower()] = full_path
                    icon_map[os.path.splitext(file)[0].lower()] = full_path
                    
    print(f"Indexed {len(icon_map)} unique icon keys.")

    # 2. Process Organization
    with open(org_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # data is { Category: [ {name, display_name, icon...}, ... ] }
    
    count_success = 0
    count_missing = 0
    
    for category, nodes in data.items():
        # Sanitize category name for folder
        safe_cat = "".join(x for x in category if (x.isalnum() or x in " ._-"))
        cat_dir = os.path.join(output_dir, safe_cat)
        os.makedirs(cat_dir, exist_ok=True)
        
        for node in nodes:
            name = node.get("name")
            display_name = node.get("display_name", name)
            icon_ref = node.get("icon")
            
            if not icon_ref:
                # Use name as fallback
                icon_ref = name

            # Strategies to find the icon:
            # 1. Exact match (lowercased)
            # 2. Kebab-case match
            # 3. Kebab-case with "icon" suffix/prefix logic if needed
            
            candidates = [
                icon_ref.lower(),
                to_kebab_case(icon_ref),
                f"{icon_ref.lower()}icon", # e.g. "Slack" -> "slackicon"
                to_kebab_case(icon_ref).replace("-", ""), # e.g. "message-square" -> "messagesquare"
            ]
            
            found_path = None
            for cand in candidates:
                if cand in icon_map:
                    found_path = icon_map[cand]
                    break
            
            # Special manual overrides if needed (e.g. specific brands)
            if not found_path:
                if "openai" in icon_ref.lower():
                    # check for common openai icon names
                     if "sparkles" in icon_map: found_path = icon_map["sparkles"] # common fallback
            
            safe_filename = "".join(x for x in display_name if (x.isalnum() or x in " ._-"))
            target_file = os.path.join(cat_dir, f"{safe_filename}.svg")
            
            if found_path:
                shutil.copy(found_path, target_file)
                count_success += 1
            else:
                # Create a placeholder or copy a default 'unknown' icon
                # print(f"Missing icon for {display_name} (ref: {icon_ref})")
                count_missing += 1

    print(f"Finished organizing.")
    print(f"Successfully matched: {count_success}")
    print(f"Missing/Not found: {count_missing}")
    print(f"Output directory: {output_dir}")

if __name__ == "__main__":
    finalize_structure()
