import os
import json
import shutil
from typing import List, Dict, Optional
from datetime import datetime

class WorkflowStore:
    """
    Manages persistence of React Flow workflows.
    Currently uses local JSON files in 'backend/saved_workflows/'.
    """
    
    def __init__(self):
        # backend/scripts/store.py -> backend/workflows/
        self.storage_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "workflows"))
        os.makedirs(self.storage_dir, exist_ok=True)
        
    def save_workflow(self, name: str, graph: Dict) -> Dict:
        """Saves a workflow to a JSON file."""
        safe_name = "".join([c for c in name if c.isalnum() or c in (' ', '-', '_')]).strip()
        filename = f"{safe_name}.json"
        path = os.path.join(self.storage_dir, filename)
        
        metadata = {
            "name": safe_name,
            "last_modified": datetime.now().isoformat(),
            "graph": graph
        }
        
        with open(path, "w", encoding="utf-8") as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)
            
        return {"status": "success", "file": filename, "path": path}
        
    def list_workflows(self) -> List[Dict]:
        """Returns a list of all saved workflows."""
        workflows = []
        for filename in os.listdir(self.storage_dir):
            if filename.endswith(".json"):
                path = os.path.join(self.storage_dir, filename)
                try:
                    with open(path, "r", encoding="utf-8") as f:
                        data = json.load(f)
                        workflows.append({
                            "name": data.get("name", filename.replace(".json", "")),
                            "last_modified": data.get("last_modified"),
                            "filename": filename
                        })
                except Exception:
                    continue # Skip corrupted files
        
        return sorted(workflows, key=lambda x: x.get("last_modified", ""), reverse=True)
        
    def load_workflow(self, filename: str) -> Optional[Dict]:
        """Loads a specific workflow by filename."""
        path = os.path.join(self.storage_dir, filename)
        if not os.path.exists(path):
            return None
            
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)

# Global singleton
workflow_store = WorkflowStore()
