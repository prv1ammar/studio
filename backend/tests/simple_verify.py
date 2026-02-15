print("Starting verification script...")
import sys
import os

print("Imports started")
# Add backend to path
current_dir = os.path.dirname(os.path.abspath(__file__)) # .../backend/tests
backend_path = os.path.abspath(os.path.join(current_dir, "..")) # .../backend
sys.path.insert(0, backend_path)
print(f"Added path: {backend_path}")

try:
    print("Importing NODE_MAP...")
    from app.nodes.factory import NODE_MAP
    print(f"NODE_MAP imported: {len(NODE_MAP)} entries")
except Exception as e:
    print(f"Failed to import NODE_MAP: {e}")
    import traceback
    traceback.print_exc()

print("Script finished.")
