"""
Obsidian-Style Markdown Node - Studio Standard
Batch 60: Knowledge Management
"""
from typing import Any, Dict, Optional, List
import os
import glob
from ...base import BaseNode
from ...registry import register_node

@register_node("obsidian_node")
class ObsidianNode(BaseNode):
    """
    Connect to local or shared Obsidian vaults.
    Optimized for structured Markdown knowledge bases with frontmatter support.
    """
    node_type = "obsidian_node"
    version = "1.0.0"
    category = "knowledge"

    inputs = {
        "action": {
            "type": "dropdown",
            "default": "read_note",
            "options": ["read_note", "write_note", "search_vault", "list_folders"],
            "description": "Obsidian action"
        },
        "vault_path": {
            "type": "string",
            "required": True,
            "description": "Local path to the Obsidian Vault"
        },
        "note_path": {
            "type": "string",
            "optional": True,
            "description": "Path to the note (e.g. 'Project/Planning.md')"
        },
        "content": {
            "type": "string",
            "optional": True,
            "description": "Content for writing"
        },
        "query": {
            "type": "string",
            "optional": True,
            "description": "Search query"
        }
    }

    outputs = {
        "result": {"type": "any"},
        "status": {"type": "string"},
        "note_metadata": {"type": "json"}
    }

    async def execute(self, input_data: Any, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        try:
            vault_path = self.get_config("vault_path")
            action = self.get_config("action", "read_note")
            note_path = self.get_config("note_path")
            
            if not os.path.isdir(vault_path):
                 return {"status": "error", "error": f"Vault path is not a directory: {vault_path}"}

            if action == "read_note":
                if not note_path:
                     return {"status": "error", "error": "Note path is required."}
                
                full_path = os.path.join(vault_path, note_path)
                if not os.path.exists(full_path):
                     return {"status": "error", "error": f"Note not found: {full_path}"}
                
                with open(full_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Basic frontmatter extraction if possible
                metadata = {}
                if content.startswith("---"):
                    parts = content.split("---", 2)
                    if len(parts) >= 3:
                        import yaml
                        try:
                            metadata = yaml.safe_load(parts[1])
                        except:
                            pass

                return {
                    "status": "success",
                    "data": {
                        "result": content,
                        "note_metadata": metadata,
                        "status": "read"
                    }
                }

            elif action == "write_note":
                if not note_path:
                     return {"status": "error", "error": "Note path is required."}
                
                content = self.get_config("content") or str(input_data)
                full_path = os.path.join(vault_path, note_path)
                
                # Ensure directories exist
                os.makedirs(os.path.dirname(full_path), exist_ok=True)
                
                with open(full_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                
                return {"status": "success", "data": {"status": "written", "path": full_path}}

            elif action == "search_vault":
                query = self.get_config("query") or str(input_data)
                # Simple glob search for demo/standard
                search_pattern = os.path.join(vault_path, "**", "*.md")
                results = []
                for file_path in glob.glob(search_pattern, recursive=True):
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        if query.lower() in f.read().lower():
                            results.append(os.path.relpath(file_path, vault_path))
                
                return {"status": "success", "data": {"result": results, "count": len(results)}}

            return {"status": "error", "error": f"Unsupported Obsidian action: {action}"}

        except Exception as e:
            return {"status": "error", "error": f"Obsidian Node Failed: {str(e)}"}
