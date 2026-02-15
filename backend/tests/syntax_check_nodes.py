import os
import py_compile
import sys

def check_syntax(directory):
    print(f"Checking syntax in {directory}...")
    success = 0
    failure = 0
    
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith(".py"):
                path = os.path.join(root, file)
                try:
                    py_compile.compile(path, doraise=True)
                    # print(f"✅ {file}")
                    success += 1
                except py_compile.PyCompileError as e:
                    print(f"❌ {file}: {e}")
                    failure += 1
                except Exception as e:
                    print(f"❌ {file}: {e}")
                    failure += 1
                    
    return success, failure

base_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "app", "nodes"))
dirs_to_check = [
    "commerce", "flow_controls", "communication", "productivity", "social_media",
    "storage", "marketing", "analytics", "support", "developer_tools", "database", "utilities"
]

total_success = 0
total_failure = 0

for d in dirs_to_check:
    full_path = os.path.join(base_path, d)
    if os.path.exists(full_path):
        s, f = check_syntax(full_path)
        total_success += s
        total_failure += f
    else:
        print(f"⚠️ Directory not found: {d}")

print("\n" + "="*50)
print(f"Syntax Check Complete: {total_success} Files Valid, {total_failure} Files Invalid")
print("="*50)
