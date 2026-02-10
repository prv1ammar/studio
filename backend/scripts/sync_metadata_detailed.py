import json
import os

def sync_detailed_metadata():
    scraping_path = r"c:\Users\info\Desktop\AI Agent Studio\scrapung_studio\Node System\component_index.json"
    output_path = r"c:\Users\info\Desktop\AI Agent Studio\backend\library_metadata.json"
    
    if not os.path.exists(scraping_path):
        print("Scraping path not found")
        return

    with open(scraping_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    # Convert to category-based dictionary
    library = {}
    
    # Add our special clinic agents first
    library["Specialists (Clinic)"] = [
        {
            "id": "booking",
            "label": "Booking Agent",
            "description": "Appointment Scheduler.",
            "color": "#00d1b2",
            "icon": "CheckCircle",
            "inputs": [{"name": "input", "type": "Text"}],
            "outputs": [{"name": "response", "type": "Text"}],
            "fields": [
                {"name": "api_key", "display_name": "API Key", "_input_type": "SecretStrInput", "required": True},
                {"name": "clinic_id", "display_name": "Clinic ID", "_input_type": "StrInput", "value": "CLINIC-001"}
            ]
        },
        {
            "id": "faq",
            "label": "Clinic FAQ Agent",
            "description": "Knowledge Base (RAG).",
            "color": "#00d1b2",
            "icon": "BookOpen",
            "inputs": [{"name": "input", "type": "Text"}],
            "outputs": [{"name": "response", "type": "Text"}],
            "fields": [
                {"name": "system_prompt", "display_name": "System Prompt", "_input_type": "MultilineInput", "multiline": True}
            ]
        },
        {
            "id": "orchestrator",
            "label": "Core Orchestrator",
            "description": "Clinic routing.",
            "color": "#00d1b2",
            "icon": "Cpu",
            "inputs": [{"name": "input", "type": "Text"}],
            "outputs": [{"name": "response", "type": "Text"}],
            "fields": []
        }
    ]

    # Map colors to categories
    CAT_COLORS = {
        "models": "#6366f1",
        "inputs": "#10b981",
        "outputs": "#f59e0b",
        "tools": "#ec4899",
        "data": "#3b82f6",
        "vectorstores": "#8b5cf6",
        "embeddings": "#06b6d4"
    }

    # Process langflow entries
    # data["entries"] is a list of [category_name, {component_name: data}]
    for entry in data.get("entries", []):
        cat_name = entry[0]
        components_dict = entry[1]
        
        if cat_name not in library:
            library[cat_name] = []
            
        for comp_name, comp_data in components_dict.items():
            # Extract relevant info for the studio
            template = comp_data.get("template", {})
            fields = []
            
            # Sort fields if field_order exists
            field_order = comp_data.get("field_order", [])
            field_keys = list(template.keys()) if not field_order else field_order
            
            for key in field_keys:
                if key == "code" or key == "_type": continue
                f_data = template.get(key)
                if not f_data or not isinstance(f_data, dict): continue
                
                # We skip hidden fields in the basic library
                if not f_data.get("show", True): continue
                
                # Append field metadata
                fields.append({
                    "name": key,
                    "display_name": f_data.get("display_name", key),
                    "_input_type": f_data.get("_input_type", "StrInput"),
                    "value": f_data.get("value", ""),
                    "options": f_data.get("options", []),
                    "info": f_data.get("info", ""),
                    "advanced": f_data.get("advanced", False),
                    "required": f_data.get("required", False)
                })

            # Build cleaned component object
            cleaned_comp = {
                "id": comp_name,
                "label": comp_data.get("display_name", comp_name),
                "description": comp_data.get("description", ""),
                "icon": comp_data.get("icon", "Cpu"),
                "color": CAT_COLORS.get(cat_name.lower(), "#666"),
                "inputs": comp_data.get("inputs", []), # This might be null for some components
                "outputs": comp_data.get("outputs", []),
                "fields": fields
            }
            
            # Fix inputs/outputs if empty using template info
            if not cleaned_comp["inputs"]:
                cleaned_comp["inputs"] = []
                for k, v in template.items():
                   if isinstance(v, dict) and v.get("type") == "other" and not v.get("tool_mode"):
                       cleaned_comp["inputs"].append({"name": k, "type": v.get("input_types", ["Any"])[0]})

            if not cleaned_comp["outputs"]:
                cleaned_comp["outputs"] = [{"name": "output", "type": "Any"}]

            library[cat_name].append(cleaned_comp)

    # Save to file
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(library, f, indent=2)
    print(f"Sync complete. {len(library)} categories processed.")

if __name__ == "__main__":
    sync_detailed_metadata()
