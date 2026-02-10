import json
import os
import sys

# Paths
SCRAPED_INDEX = r"c:/Users/PC/Pictures/scrapung_studio/Node System/component_index.json"
# We read from scraped index but now we know files are moved. 
# Actually, we can still read the scraped index as the source of truth for "what exists".
OUTPUT_METADATA = r"c:/Users/PC/Pictures/studio_tyboo-main/backend/data/library_metadata.json"


def convert_type(lfx_type):
    """Maps Langflow types to Studio types."""
    if lfx_type in ["str", "String"]: return "Text"
    if lfx_type in ["dict", "Data"]: return "Any"
    if lfx_type == "LanguageModel": return "LanguageModel"
    if lfx_type == "Embeddings": return "Embeddings"
    return "Any"

def ingest():
    print(f"Reading from {SCRAPED_INDEX}...")
    try:
        with open(SCRAPED_INDEX, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        print(f"Error reading index: {e}")
        return
    
    entries = data.get("entries", [])


    try:
        if os.path.exists(OUTPUT_METADATA):
            with open(OUTPUT_METADATA, "r", encoding="utf-8") as f:
                library = json.load(f)
            print(f"Loaded existing library with {len(library)} categories.")
        else:
            library = {}
            print("No existing library found. Creating new.")
    except Exception as e:
        print(f"Error reading existing library: {e}")
        library = {}

    # Ensure defaults exist (softly)
    if "Studio Essentials" not in library: library["Studio Essentials"] = []
    if "Tyboo Custom" not in library: library["Tyboo Custom"] = []

    print(f"Found {len(entries)} component categories in scraped index.")

    for entry in entries:
        category_name = entry[0]
        # Map scraped category names to nicer Studio names if needed?
        # e.g. "FAISS" -> "Vector Stores" ?
        # Langflow index seems to have specific headers like "FAISS", "Notion". 
        # The user wants "same way Langflow does". Langflow sidebar IS these categories.
        # But maybe grouped?
        # In the component_index.json, "entries" is a list of [Category, {Components}].
        # So "FAISS" IS the category.
        
        components = entry[1]
        
        # Merge logic:
        # If category exists, we add unique items.
        if category_name not in library:
            library[category_name] = []
            
        current_ids = {c["id"] for c in library[category_name]}

        
        # ... (rest of logic) ...

        
        studio_components = []
        
        for comp_name, comp_data in components.items():
            try:
                # Basic Metadata
                node_id = comp_name
                label = comp_data.get("display_name", comp_name)
                description = comp_data.get("description", "")
                icon = comp_data.get("icon", "Box")
                
                # Inputs (Fields)
                inputs = []
                fields = []
                template = comp_data.get("template", {})
                
                for field_name, field_data in template.items():
                    if field_name == "_type": continue
                    if field_name == "code": continue # Skip code field for UI, relevant for backend
                    
                    is_input = field_data.get("show", True)
                    input_type = field_data.get("type", "str")
                    
                    # Create Studio Field
                    field_def = {
                        "name": field_name,
                        "display_name": field_data.get("display_name", field_name),
                        "_input_type": field_data.get("_input_type", "StrInput"),
                        "info": field_data.get("info", ""),
                        "value": field_data.get("value"),
                        "required": field_data.get("required", False),
                        "advanced": field_data.get("advanced", False)
                    }
                    if "options" in field_data:
                        field_def["options"] = field_data["options"]
                        
                    fields.append(field_def)
                    
                    # Create Studio Input (Port) if applicable
                    # Logic: In Langflow, HandleInput usually means a port.
                    if "HandleInput" in field_def["_input_type"] or \
                       field_data.get("input_types"): 
                        inputs.append({
                            "name": field_name,
                            "type": convert_type(field_data.get("input_types", ["Any"])[0])
                        })

                # Outputs
                outputs = []
                # Langflow outputs are in 'outputs' list
                lf_outputs = comp_data.get("outputs", [])
                for out in lf_outputs:
                    outputs.append({
                        "name": out.get("name"),
                        "display_name": out.get("display_name"),
                        "type": convert_type(out.get("types", ["Any"])[0]),
                        "method": out.get("method") # Important for execution
                    })
                
                # Metadata for Execution
                # Store the module path so engine.py can find it
                metadata = comp_data.get("metadata", {})
                # Add to fields as hidden? Or just keep in the node object. 
                # Studio metadata format isn't strictly defined, but we can add extra keys.
                
                node = {
                    "id": node_id,
                    "label": label,
                    "description": description,
                    "icon": icon,
                    "color": "#666", # Default gray
                    "inputs": inputs,
                    "outputs": outputs,
                    "fields": fields,
                    "execution_metadata": metadata # Custom field for our engine
                }
                
                if node_id not in current_ids:
                    library[category_name].append(node)
                    current_ids.add(node_id)

                
                
            except Exception as e:
                print(f"Skipping {comp_name}: {e}")
                continue


    # Write output
    print(f"Writing {len(library)} categories to {OUTPUT_METADATA}...")
    with open(OUTPUT_METADATA, "w", encoding="utf-8") as f:
        json.dump(library, f, indent=2)
    print("Done.")

if __name__ == "__main__":
    ingest()
