import sys
import os
import json
import inspect

# Add project root and backend to path
project_root = os.path.abspath(os.getcwd())
backend_path = os.path.join(project_root, "backend")
if backend_path not in sys.path:
    sys.path.insert(0, backend_path)

from app.nodes.registry import NodeRegistry
from app.nodes.base import BaseNode

def sync():
    print("Pre-scan registry size:", len(NodeRegistry._nodes))
    NodeRegistry.scan_and_register()
    print("Post-scan registry size:", len(NodeRegistry._nodes))
    
    migrated_list = []
    
    for node_id, node_class in NodeRegistry._nodes.items():
        print(f"Processing node: {node_id} (Class: {node_class.__name__})")
        
        # We WANT the adapters too, as they wrap the actual components
        # But we need to handle them correctly.
        
        try:
            # Instantiate to get schema info if possible
            # Note: some might fail if they require specific config in __init__
            instance = None
            try:
                instance = node_class()
            except Exception as e:
                print(f"  Could not instantiate {node_id}: {e}")
                continue

            # Basic node definition
            node_def = {
                "id": node_id,
                "name": f"{node_id.replace('_node', '').replace('_', ' ').title()} (Native)",
                "label": node_id.replace('_node', '').replace('_', ' ').title(),
                "description": node_class.__doc__.strip() if node_class.__doc__ else f"Native {node_id} integration.",
                "category": "Native Integrations",
                "icon": "Box",
                "color": "#3b82f6",
                "inputs": [],
                "outputs": []
            }

            # Try to get more info from the instance
            if hasattr(instance, "category") and instance.category:
                node_def["category"] = "Native Integrations" # We group them here for visibility
                
            if hasattr(instance, "icon") and instance.icon:
                node_def["icon"] = instance.icon
            if hasattr(instance, "color") and instance.color:
                node_def["color"] = instance.color

            # Process inputs
            inputs_dict = getattr(node_class, "inputs", {})
            if not inputs_dict and hasattr(instance, "inputs"):
                inputs_dict = instance.inputs
                
            for name, spec in inputs_dict.items():
                input_def = {
                    "name": name,
                    "display_name": name.replace('_', ' ').title(),
                    "type": spec.get("type", "text"),
                    "required": spec.get("required", False)
                }
                if "options" in spec: input_def["options"] = spec["options"]
                if "default" in spec: input_def["default"] = spec["default"]
                if "description" in spec: input_def["description"] = spec["description"]
                node_def["inputs"].append(input_def)

            # Ensure every node has a default input handle (unless it's a trigger)
            has_explicit_handle = any(i.get("type") == "handle" or i["name"] == "input" for i in node_def["inputs"])
            is_trigger = node_def.get("category") == "Triggers" or "trigger" in node_id.lower()
            
            if not has_explicit_handle and not is_trigger:
                node_def["inputs"].append({
                    "name": "input",
                    "display_name": "Input",
                    "type": "handle",
                    "required": False,
                    "description": "Main data input"
                })

            # Process credentials
            creds = getattr(node_class, "credentials_required", [])
            if not creds and hasattr(instance, "credentials_required"):
                creds = instance.credentials_required
                
            for cred_key in creds:
                node_def["inputs"].insert(0, {
                    "name": cred_key,
                    "display_name": cred_key.replace('_', ' ').title(),
                    "type": "credential",
                    "required": True
                })

            # Process outputs
            outputs_dict = getattr(node_class, "outputs", {})
            if not outputs_dict and hasattr(instance, "outputs"):
                outputs_dict = instance.outputs
                
            for name, spec in outputs_dict.items():
                output_def = {
                    "name": name,
                    "display_name": name.replace('_', ' ').title(),
                    "types": [spec.get("type", "Any").title()]
                }
                node_def["outputs"].append(output_def)

            # Process n8n-style properties
            props = getattr(node_class, "properties", [])
            if not props and hasattr(instance, "properties"):
                props = instance.properties
            if props:
                node_def["properties"] = props
            
            migrated_list.append(node_def)
            
        except Exception as e:
            print(f"  Error processing {node_id}: {e}")

    # Write to file
    output_path = os.path.join(backend_path, "data", "migrated_nodes.json")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump({"Native Integrations": migrated_list}, f, indent=2)
    
    print(f"Finished writing {len(migrated_list)} nodes to {output_path}")

if __name__ == "__main__":
    sync()
