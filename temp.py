import os
import ast
import json
import re

NODES_DIR = "backend/app/nodes"

def map_type(old_type):
    mapping = {
        "text": "string",
        "int": "number",
        "float": "number",
        "boolean": "boolean",
        "bool": "boolean",
        "dropdown": "options",
        "multiselect": "multiOptions",
        "dict": "json",
        "code": "json",
        "file": "string", # Files are often paths
    }
    return mapping.get(old_type.lower(), "string")

def transform_input_def(name, spec):
    """
    Transforms a legacy input definition dict into an n8n property dict.
    """
    # Extract basic fields
    # Note: spec is an AST dict node, so we need to evaluate it safely or parse it manually
    # For simplicity in this script, we'll assume we have the python dict already
    
    new_prop = {
        "displayName": spec.get("display_name", name.replace("_", " ").title()),
        "name": name,
        "type": map_type(spec.get("type", "text")),
        "default": spec.get("default", ""),
    }

    if "options" in spec:
        # Convert simple list ["a", "b"] to [{"name": "A", "value": "a"}, ...]
        opts = spec["options"]
        if opts and isinstance(opts[0], str):
            new_prop["options"] = [{"name": o.replace("_", " ").title(), "value": o} for o in opts]
        else:
            new_prop["options"] = opts # Assume already in correct format
            
    if "description" in spec:
        new_prop["description"] = spec["description"]
        
    if spec.get("required", False):
        new_prop["required"] = True
        
    # Heuristic for Resource/Operation mapping
    if name == "action":
        new_prop["name"] = "operation"
        new_prop["displayName"] = "Operation"
        
    return new_prop

import sys

def generate_properties_code(inputs_dict):
    """
    Generates Python code for the properties list based on the inputs dict.
    """
    properties = []
    sorted_items = sorted(inputs_dict.items()) # Stability
    
    # Heuristic: Move 'action' to the top if present
    action_item = next((item for item in sorted_items if item[0] == 'action'), None)
    if action_item:
        sorted_items.remove(action_item)
        sorted_items.insert(0, action_item)

    for name, spec in sorted_items:
        # Normalize spec to dict if it's not (though usually it is)
        if not isinstance(spec, dict):
            spec = {}
            
        prop = transform_input_def(name, spec)
        properties.append(prop)

    # Generate the code string
    code_lines = ["    properties = ["]
    for prop in properties:
        code_lines.append("        {")
        for key, value in prop.items():
            if isinstance(value, str):
                code_lines.append(f"            '{key}': '{value}',")
            elif isinstance(value, bool):
                code_lines.append(f"            '{key}': {str(value)},")
            elif isinstance(value, list) and key == 'options':
                code_lines.append(f"            '{key}': [")
                for opt in value:
                    code_lines.append(f"                {{'name': '{opt['name']}', 'value': '{opt['value']}'}},")
                code_lines.append("            ],")
            else:
                 code_lines.append(f"            '{key}': {repr(value)},")
        code_lines.append("        },")
    code_lines.append("    ]")
    return "\n".join(code_lines)

def migrate_node_file(file_path, dry_run=True):
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        tree = ast.parse(content)
        
        # Find the inputs assignment
        inputs_assign = None
        node_class = None
        
        for node in tree.body:
            if isinstance(node, ast.ClassDef):
                if any(b.id == 'BaseNode' for b in list(filter(lambda x: isinstance(x, ast.Name), node.bases))):
                    node_class = node
                    break
                    
        if not node_class: return

        # Check for existing properties
        has_properties = False
        for item in node_class.body:
            if isinstance(item, ast.Assign):
                for target in item.targets:
                    if isinstance(target, ast.Name):
                        if target.id == 'inputs':
                            inputs_assign = item
                        elif target.id == 'properties':
                            has_properties = True
        
        if not inputs_assign or has_properties:
            return

        print(f"Migrating {file_path}...")

        # Extract dictionary content safely
        # We find the line range of the inputs assignment
        start_line = inputs_assign.lineno
        end_line = inputs_assign.end_lineno
        
        # Extract the text of the dict and eval it (safe-ish context)
        inputs_text = "\n".join(content.splitlines()[start_line-1:end_line])
        # We need just the dict part, so we split by '='
        if '=' in inputs_text:
            dict_text = inputs_text.split('=', 1)[1].strip()
            try:
                inputs_dict = ast.literal_eval(dict_text)
            except Exception:
                # Fallback: regex extraction if AST eval fails (e.g. specialized types)
                print(f"  Warning: Could not literal_eval inputs for {file_path}. Skipping.")
                return
        else:
             return

        # Generate new code
        new_properties_code = generate_properties_code(inputs_dict)
        
        if dry_run:
            print(f"  [Dry Run] Would insert properties block before line {start_line}")
            # print(new_properties_code)
        else:
            # Insert logic
            lines = content.splitlines()
            # Insert before the inputs definition
            lines.insert(start_line - 1, new_properties_code)
            lines.insert(start_line - 1, "") # Add blank line
            
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write("\n".join(lines))
            print(f"  [Success] Updated {file_path}")

    except Exception as e:
        print(f"  Error processing {file_path}: {e}")

if __name__ == "__main__":
    write_mode = "--write" in sys.argv
    print(f"Starting migration (Write Mode: {write_mode})...")
    
    for root, _, files in os.walk(NODES_DIR):
        for file in files:
            if file.endswith(".py") and file != "base.py" and file != "__init__.py":
                migrate_node_file(os.path.join(root, file), dry_run=not write_mode)
