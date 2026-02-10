import json
import os

def sync_library():
    """
    Translates the internal 'True' Langflow metadata into the 
    App-compatible 'library_metadata.json'.
    Ensures EXACT Display Names and AUTHENTIC Icon strings are preserved.
    """
    try:
        source_path = "backend/true_langflow_library.json"
        if not os.path.exists(source_path):
            print("Source metadata not found.")
            return

        with open(source_path, "r", encoding="utf-8") as f:
            true_lib = json.load(f)

        final_library = {
            "Specialists (Clinic)": [
                {"id": "faq", "label": "Clinic FAQ Agent", "description": "Knowledge Base (RAG).", "color": "#00d1b2", "icon": "BookOpen", "inputs": [{"name": "input", "type": "Text"}], "outputs": [{"name": "response", "type": "Text"}], "fields": [{"name": "system_prompt", "type": "str", "multiline": True}]},
                {"id": "booking", "label": "Booking Agent", "description": "Appointment Scheduler.", "color": "#00d1b2", "icon": "CheckCircle", "inputs": [{"name": "input", "type": "Text"}], "outputs": [{"name": "response", "type": "Text"}], "fields": [{"name": "api_key", "type": "str"}]},
                {"id": "patient", "label": "Patient Agent", "description": "Records manager.", "color": "#00d1b2", "icon": "User", "inputs": [{"name": "input", "type": "Text"}], "outputs": [{"name": "response", "type": "Text"}], "fields": []},
                {"id": "orchestrator", "label": "Core Orchestrator", "description": "Clinic routing.", "color": "#00d1b2", "icon": "Cpu", "inputs": [{"name": "input", "type": "Text"}], "outputs": [{"name": "response", "type": "Text"}], "fields": []}
            ]
        }

        # Categories mapping
        cat_map = {
            "agents": "Agents",
            "models": "Models",
            "embeddings": "Models",
            "prompts": "Prompts",
            "input_output": "Inputs",
            "loaders": "Inputs",
            "tools": "Tools",
            "chains": "Chains",
            "logic": "Control & Logic",
            "vectorstores": "Vector Stores",
            "memories": "Memory",
            "mcp": "MCP / External",
            "helpers": "Helpers",
            "processing": "Processing",
            "data": "Data"
        }

        for cat_key, components in true_lib.items():
            ui_cat = "Others"
            l_key = cat_key.lower()
            for k, v in cat_map.items():
                if k in l_key:
                    ui_cat = v
                    break
            
            if ui_cat not in final_library:
                final_library[ui_cat] = []

            for comp_id, comp_data in components.items():
                if not isinstance(comp_data, dict): continue
                
                # EXACT name from Langflow
                label = comp_data.get("display_name", comp_id)
                icon = comp_data.get("icon", "Cpu")
                description = comp_data.get("description", "")
                
                # Authentic Sockets (Heuristic from outputs/inputs if available)
                inputs = []
                outputs = []
                
                if "outputs" in comp_data and isinstance(comp_data["outputs"], list):
                    for out in comp_data["outputs"]:
                        if isinstance(out, dict):
                            out_types = out.get("types", ["Any"])
                            outputs.append({"name": out.get("display_name", out.get("name", "Output")), "type": out_types[0]})

                # If no outputs found in struct, add a default
                if not outputs:
                    outputs = [{"name": "Output", "type": "Any"}]

                # Basic Component Struct
                info = {
                    "id": comp_id,
                    "label": label, # EXACT MATCH
                    "icon": icon,   # AUTHENTIC ICON STRING
                    "description": description,
                    "color": comp_data.get("color", "#818cf8"),
                    "inputs": [{"name": "Input", "type": "Any"}],
                    "outputs": outputs,
                    "fields": []
                }
                
                # Apply high-fidelity Langflow Category Colors if missing
                if not comp_data.get("color"):
                    if ui_cat == "Models": info["color"] = "#818cf8"
                    elif ui_cat == "Inputs": info["color"] = "#22c55e"
                    elif ui_cat == "Agents": info["color"] = "#6366f1"
                    elif ui_cat == "Prompts": info["color"] = "#f59e0b"
                    elif ui_cat == "Tools": info["color"] = "#ec4899"
                    elif ui_cat == "Vector Stores": info["color"] = "#8b5cf6"
                
                # Add Fields from Template
                template = comp_data.get("template", {})
                for f_name, f_info in template.items():
                    if f_name.startswith("_"): continue
                    if not isinstance(f_info, dict): continue
                    info["fields"].append({
                        "name": f_name,
                        "label": f_info.get("display_name", f_name),
                        "type": f_info.get("type", "str"),
                        "multiline": f_info.get("multiline", False),
                        "default": f_info.get("value"),
                        "info": f_info.get("info", "")
                    })

                final_library[ui_cat].append(info)

        # Remove duplicates and sort
        for cat in final_library:
            seen = set()
            unique_items = []
            for item in final_library[cat]:
                if item["label"] not in seen:
                    seen.add(item["label"])
                    unique_items.append(item)
            final_library[cat] = sorted(unique_items, key=lambda x: x["label"])

        with open("backend/library_metadata.json", "w", encoding="utf-8") as f:
            json.dump(final_library, f, indent=2)

        print(f"Propagated Authentic metadata for {sum(len(v) for v in final_library.values())} components.")
    except Exception as e:
        import traceback
        print(f"Sync Error: {e}")
        traceback.print_exc()

if __name__ == "__main__":
    sync_library()
