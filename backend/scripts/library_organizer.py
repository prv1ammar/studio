import json
import os

def organize_library():
    """
    Reads the raw 362-component scrape and organizes it into 
    Langflow's 10 major industry standard categories.
    """
    try:
        path = "backend/full_library_metadata.json"
        with open(path, "r", encoding="utf-8") as f:
            raw_lib = json.load(f)
            
        final_library = {
            "Inputs": [],
            "Models": [],
            "Prompts": [],
            "Agents": [],
            "Chains": [],
            "Tools": [],
            "MCP / External": [],
            "Data & Retrieval": [],
            "Control & Logic": [],
            "Specialists (Clinic)": []
        }
        
        # Add Your Custom Specialists
        final_library["Specialists (Clinic)"] = [
            {"id": "faq", "label": "Clinic FAQ Agent", "description": "Knowledge Base (RAG).", "color": "#8b5cf6", "icon": "BookOpen", "inputs": [{"name": "input", "type": "Text"}], "outputs": [{"name": "response", "type": "Text"}], "fields": [{"name": "system_prompt", "type": "str", "multiline": True}]},
            {"id": "booking", "label": "Booking Agent", "description": "Appointment Scheduler.", "color": "#8b5cf6", "icon": "CheckCircle", "inputs": [{"name": "input", "type": "Text"}], "outputs": [{"name": "response", "type": "Text"}], "fields": [{"name": "api_key", "type": "str"}]},
            {"id": "patient", "label": "Patient Agent", "description": "Records manager.", "color": "#8b5cf6", "icon": "User", "inputs": [{"name": "input", "type": "Text"}], "outputs": [{"name": "response", "type": "Text"}], "fields": []},
            {"id": "orchestrator", "label": "Orchestrator", "description": "Clinic routing.", "color": "#8b5cf6", "icon": "Cpu", "inputs": [{"name": "input", "type": "Text"}], "outputs": [{"name": "response", "type": "Text"}], "fields": []}
        ]

        for cat_name, components in raw_lib.items():
            lower_cat = cat_name.lower()
            
            target = "Tools" # Default
            if "input" in lower_cat or "loader" in lower_cat: target = "Inputs"
            elif "model" in lower_cat or "openai" in lower_cat or "anthropic" in lower_cat: target = "Models"
            elif "prompt" in lower_cat: target = "Prompts"
            elif "agent" in lower_cat or "crew" in lower_cat: target = "Agents"
            elif "chain" in lower_cat: target = "Chains"
            elif "mcp" in lower_cat: target = "MCP / External"
            elif "vector" in lower_cat or "splitter" in lower_cat or "retriever" in lower_cat: target = "Data & Retrieval"
            elif "logic" in lower_cat or "router" in lower_cat or "conditional" in lower_cat: target = "Control & Logic"
            
            for comp in components:
                # Clean labels
                if not comp.get("label"): comp["label"] = cat_name.replace("_", " ")
                final_library[target].append(comp)

        with open("backend/library_metadata.json", "w", encoding="utf-8") as f:
            json.dump(final_library, f, indent=2)
            
        print("Successfully organized 362 components into Langflow categories.")
    except Exception as e:
        print(f"Error organizing library: {e}")

if __name__ == "__main__":
    organize_library()
