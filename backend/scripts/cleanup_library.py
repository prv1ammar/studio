import json
import os

def cleanup_all_json_files():
    data_dir = "backend/data"
    for filename in os.listdir(data_dir):
        if filename.endswith(".json"):
            path = os.path.join(data_dir, filename)
            with open(path, "r", encoding="utf-8") as f:
                try:
                    data = json.load(f)
                except:
                    continue

            # Recursive function to remove composio from dicts/lists
            def purge_composio(obj):
                if isinstance(obj, dict):
                    return {k: purge_composio(v) for k, v in obj.items() if "composio" not in str(v).lower() and "composio" not in k.lower()}
                elif isinstance(obj, list):
                    return [purge_composio(i) for i in obj if "composio" not in str(i).lower()]
                return obj

            cleaned_data = purge_composio(data)

            with open(path, "w", encoding="utf-8") as f:
                json.dump(cleaned_data, f, indent=2)
            print(f"Purged Composio from {filename}")

if __name__ == "__main__":
    cleanup_all_json_files()
