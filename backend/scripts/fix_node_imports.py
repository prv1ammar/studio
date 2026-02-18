import os
import re

def fix_imports():
    nodes_dir = os.path.join("backend", "app", "nodes")
    
    for root, dirs, files in os.walk(nodes_dir):
        for file in files:
            if file.endswith(".py"):
                file_path = os.path.join(root, file)
                
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()
                
                # Calculate depth relative to app/nodes
                rel_path = os.path.relpath(root, nodes_dir)
                depth = 0 if rel_path == "." else len(rel_path.split(os.sep))
                
                # If depth is 1 (e.g. app/nodes/communication/), we need ..base
                # If depth is 2 (e.g. app/nodes/storage/nocodb/), we need ...base
                
                new_content = content
                if depth == 1:
                    # Change ...base to ..base
                    new_content = re.sub(r"from \.\.\.base import BaseNode", r"from ..base import BaseNode", new_content)
                    new_content = re.sub(r"from \.\.\.registry import register_node", r"from ..registry import register_node", new_content)
                    # Also handle factory if any
                    new_content = re.sub(r"from \.\.\.factory import register_node", r"from ..factory import register_node", new_content)
                
                if new_content != content:
                    with open(file_path, "w", encoding="utf-8") as f:
                        f.write(new_content)
                    print(f"Fixed imports in {file_path} (depth {depth})")

if __name__ == "__main__":
    fix_imports()
