import sys
import os

# Add project root and backend to path
project_root = os.path.abspath(os.getcwd())
backend_path = os.path.join(project_root, "backend")
if backend_path not in sys.path:
    sys.path.insert(0, backend_path)

from app.nodes.registry import NodeRegistry

def check():
    print("Starting scan...")
    NodeRegistry.scan_and_register()
    keys = sorted(list(NodeRegistry._nodes.keys()))
    with open("registry_keys.txt", "w") as f:
        for k in keys:
            f.write(f"{k}\n")
    print(f"Done. Found {len(keys)} nodes.")

if __name__ == "__main__":
    check()
