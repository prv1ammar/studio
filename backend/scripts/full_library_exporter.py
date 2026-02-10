import json
import logging
import pkgutil
import langflow.components
import inspect
from typing import Dict, List, Any

def get_component_info(component_class):
    """Extracts metadata from a Langflow component class."""
    try:
        # Instantiate if possible to get full template
        instance = component_class()
        
        # Basic Info
        info = {
            "id": component_class.__name__,
            "label": getattr(instance, "display_name", component_class.__name__),
            "description": getattr(instance, "description", ""),
            "color": getattr(instance, "color", "#818cf8"),
            "icon": getattr(instance, "icon", "Cpu"),
            "inputs": [],
            "outputs": [],
            "fields": []
        }
        
        # Extract Inputs/Outputs if available in newer Langflow versions
        if hasattr(instance, "inputs"):
            for inp in instance.inputs:
                info["inputs"].append({"name": inp.name, "type": getattr(inp, "input_types", ["Any"])[0]})
        
        if hasattr(instance, "outputs"):
            for out in instance.outputs:
                info["outputs"].append({"name": out.name, "type": getattr(out, "output_types", ["Any"])[0]})

        # Extract Template (Fields)
        if hasattr(instance, "template"):
            template = instance.template
            for field_name, field_obj in template.items():
                if field_name.startswith("_"): continue
                field_info = {
                    "name": field_name,
                    "type": getattr(field_obj, "type", "str"),
                    "multiline": getattr(field_obj, "multiline", False),
                    "options": getattr(field_obj, "options", None),
                    "default": getattr(field_obj, "value", None)
                }
                info["fields"].append(field_info)
                
        return info
    except Exception:
        return None

def build_full_library():
    library = {}
    
    # Iterate through all submodules in langflow.components
    for loader, module_name, is_pkg in pkgutil.walk_packages(langflow.components.__path__, langflow.components.__name__ + "."):
        try:
            module = loader.find_module(module_name).load_module(module_name)
            category = module_name.split(".")[-1].capitalize()
            
            if category not in library:
                library[category] = []
                
            # Find all classes in this module
            for name, obj in inspect.getmembers(module, inspect.isclass):
                # Try to filter for components (heuristic)
                if hasattr(obj, "display_name") or "Component" in [base.__name__ for base in obj.__mro__]:
                    info = get_component_info(obj)
                    if info:
                        library[category].append(info)
        except Exception:
            continue
            
    # Clean up empty categories
    library = {k: v for k, v in library.items() if v}
    
    with open("backend/full_library_metadata.json", "w", encoding="utf-8") as f:
        json.dump(library, f, indent=2)
    
    print(f"Exported {sum(len(v) for v in library.values())} components across {len(library)} categories.")

if __name__ == "__main__":
    build_full_library()
