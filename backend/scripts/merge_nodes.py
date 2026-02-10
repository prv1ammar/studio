import os
import shutil

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
SOURCE = os.path.join(ROOT, "backend", "app", "nodes", "imported")
DEST = os.path.join(ROOT, "backend", "app", "nodes")

def merge_folders():
    if not os.path.exists(SOURCE):
        print("Source not found")
        return

    for item in os.listdir(SOURCE):
        s_path = os.path.join(SOURCE, item)
        d_path = os.path.join(DEST, item)
        
        if os.path.isdir(s_path):
            if os.path.exists(d_path):
                print(f"Merging {item}...")
                for sub_item in os.listdir(s_path):
                    ss_path = os.path.join(s_path, sub_item)
                    dd_path = os.path.join(d_path, sub_item)
                    if os.path.isdir(ss_path):
                         shutil.copytree(ss_path, dd_path, dirs_exist_ok=True)
                    else:
                         shutil.copy2(ss_path, dd_path)
            else:
                print(f"Moving {item}...")
                shutil.move(s_path, d_path)
        else:
            # It's a file (like component_index.json)
            shutil.copy2(s_path, d_path)

    print("✅ Merge complete.")
    # Clean up
    if os.path.exists(SOURCE) and not os.listdir(SOURCE):
         os.rmdir(SOURCE)

if __name__ == "__main__":
    merge_folders()
