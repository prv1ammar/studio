import os
import ast
import json
import re
from collections import defaultdict

NODES_DIR = "backend/app/nodes"

def get_python_files(directory):
    py_files = []
    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith(".py") and file != "__init__.py" and "__pycache__" not in root:
                py_files.append(os.path.join(root, file))
    return py_files

def analyze_file(file_path):
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    try:
        tree = ast.parse(content)
    except Exception as e:
        return {"error": str(e), "file": file_path}

    nodes_found = []
    has_lfx = "from lfx" in content or "import lfx" in content

    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            # Identification criteria
            is_potential_node = False
            
            # 1. Inherits from BaseNode or Component
            for base in node.bases:
                base_name = ""
                if isinstance(base, ast.Name): base_name = base.id
                elif isinstance(base, ast.Attribute): base_name = base.attr
                
                if base_name in ["BaseNode", "Component", "CustomComponent"]:
                    is_potential_node = True
                if "Node" in base_name or "Component" in base_name:
                    is_potential_node = True

            # 2. Has specific methods
            methods = [item.name for item in node.body if isinstance(item, ast.FunctionDef)]
            if any(m in ["execute", "run", "build", "fetch_content"] for m in methods):
                is_potential_node = True
            
            # 3. Has inputs/outputs attributes
            class_attrs = []
            for item in node.body:
                if isinstance(item, (ast.Assign, ast.AnnAssign)):
                    targets = item.targets if isinstance(item, ast.Assign) else [item.target]
                    for t in targets:
                        if isinstance(t, ast.Name): class_attrs.append(t.id)
            
            if "inputs" in class_attrs or "outputs" in class_attrs:
                is_potential_node = True

            if is_potential_node:
                node_info = {
                    "name": node.name,
                    "file": file_path,
                    "is_legacy": has_lfx or "Component" in [b.id if isinstance(b, ast.Name) else "" for b in node.bases],
                    "has_node_law": False,
                    "issues": [],
                    "metadata": {}
                }
                
                # Check Node Law
                metadata_keys = set()
                for item in node.body:
                    if isinstance(item, (ast.Assign, ast.AnnAssign)):
                        targets = item.targets if isinstance(item, ast.Assign) else [item.target]
                        for t in targets:
                             if isinstance(t, ast.Name): 
                                 metadata_keys.add(t.id)
                                 if isinstance(item, ast.Assign) and isinstance(item.value, ast.Constant):
                                     node_info["metadata"][t.id] = item.value.value

                if "node_type" in metadata_keys and "version" in metadata_keys and "category" in metadata_keys:
                    node_info["has_node_law"] = True
                else:
                    if "node_type" not in metadata_keys: node_info["issues"].append("missing_node_type")
                    if "version" not in metadata_keys: node_info["issues"].append("missing_version")
                    if "category" not in metadata_keys: node_info["issues"].append("missing_category")

                nodes_found.append(node_info)

    return nodes_found

def main():
    files = get_python_files(NODES_DIR)
    print(f"Auditing {len(files)} files...")
    
    report = {
        "total_files": len(files),
        "total_nodes_found": 0,
        "legacy_nodes": 0,
        "standardized_nodes": 0,
        "details": []
    }
    
    for file_path in files:
        results = analyze_file(file_path)
        if isinstance(results, dict) and "error" in results: continue
        
        for node in results:
            report["total_nodes_found"] += 1
            if node["is_legacy"]:
                report["legacy_nodes"] += 1
            elif node["has_node_law"]:
                report["standardized_nodes"] += 1
            
            report["details"].append(node)

    with open("GLOBAL_NODE_AUDIT.json", "w") as f:
        json.dump(report, f, indent=2)
        
    print(f"Audit Complete.")
    print(f"Nodes Found: {report['total_nodes_found']}")
    print(f"Legacy (Langflow): {report['legacy_nodes']}")
    print(f"Standardized (Studio): {report['standardized_nodes']}")
    print(f"Uncategorized: {report['total_nodes_found'] - report['legacy_nodes'] - report['standardized_nodes']}")

if __name__ == "__main__":
    main()
