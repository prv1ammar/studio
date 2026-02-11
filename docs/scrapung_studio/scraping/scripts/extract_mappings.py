
import re

def extract_mappings_and_search_definitions():
    bundle_path = r"c:\Users\info\Desktop\Nouveau dossier (2)\venv\Lib\site-packages\langflow\frontend\assets\index-BVZrupat.js"
    
    with open(bundle_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 1. Extract Mappings
    # Pattern:  Key:"Value"
    # We saw a block full of them, separated by commas.
    # regex:  ([a-zA-Z0-9_]+):"([a-zA-Z0-9_]+)"
    
    mappings = re.findall(r'([a-zA-Z0-9_]+):"([a-zA-Z0-9_]+)"', content)
    
    print(f"Found {len(mappings)} mappings.")
    
    # Save mappings to a python file or print them
    mapping_dict = dict(mappings)
    
    # 2. Search for "Notion" definition
    # It might be in an object { Notion: ..., Google: ... }
    # Or export { Notion, Google }
    
    # Let's look for where "Notion" is a key in an object BUT associated with a function or variable, not a string.
    # e.g. Notion:e5, or Notion:function()...
    
    # Regex for Notion key:  Notion:([^",\}]+)
    notion_matches = re.findall(r'Notion:([^",\}]+)', content)
    print("Potential Notion definitions:", notion_matches)

    # Regex for Google key: Google:([^",\}]+)
    google_matches = re.findall(r'Google:([^",\}]+)', content)
    print("Potential Google definitions:", google_matches)

    # Let's also dump the mapping to a file we can import
    with open("extracted_mappings.py", "w", encoding='utf-8') as f:
        f.write("icon_mappings = " + str(mapping_dict))

if __name__ == "__main__":
    extract_mappings_and_search_definitions()
