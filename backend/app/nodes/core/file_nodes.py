import os
from typing import Any, Dict, Optional
from ..base import BaseNode
from ..registry import register_node

class FileBaseNode(BaseNode):
    """Base class for file operations with sandboxing."""
    category = "logic"
    version = "1.0.0"
    
    def _get_safe_path(self, user_path: str):
        """
        Sandboxing logic to prevent directory traversal and restrict access
        to the project's sandbox directory.
        """
        # Resolve the project root (4 levels up from backend/app/nodes/core/)
        core_dir = os.path.dirname(os.path.abspath(__file__))
        workspace_root = os.path.abspath(os.path.join(core_dir, "..", "..", "..", ".."))
        
        # Normalize the user path to prevent '../' tricks
        normalized_user_path = os.path.normpath(user_path).replace("\\", "/")
        # print(f"DEBUG: user_path={user_path}, normalized={normalized_user_path}")
        
        if normalized_user_path.startswith("..") or normalized_user_path.startswith("/") or (len(normalized_user_path) > 1 and normalized_user_path[1] == ":"):
            # Block absolute paths (Windows C:/ or Unix /) and directory traversal
            raise ValueError(f"Access denied: path '{user_path}' is invalid or attempts to escape the sandbox.")
        
        # Determine base directory (defaults to 'outputs' in the project root)
        base_dir_name = self.get_config("base_dir", "outputs")
        full_base_dir = os.path.join(workspace_root, base_dir_name)
        
        # Ensure the base directory exists
        if not os.path.exists(full_base_dir):
            os.makedirs(full_base_dir, exist_ok=True)
            
        # Combine base and user path
        full_path = os.path.abspath(os.path.join(full_base_dir, normalized_user_path))
        
        # Final safety check: ensure the resolved path is still within the base directory
        if not full_path.startswith(full_base_dir):
            raise ValueError(f"Access denied: path '{user_path}' is outside of the sandbox '{base_dir_name}'")
            
        return full_path

@register_node("read_file")
class ReadFileNode(FileBaseNode):
    """Reads the content of a file within the sandbox."""
    node_type = "read_file"
    inputs = {
        "file_path": {"type": "string", "description": "Path relative to sandbox root"}
    }
    outputs = {
        "content": {"type": "string"},
        "status": {"type": "string"}
    }

    async def execute(self, input_data: Any, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        try:
            path_str = self.get_config("file_path") or (input_data if isinstance(input_data, str) else "")
            if not path_str:
                return {"status": "error", "error": "File path is required."}
                
            safe_path = self._get_safe_path(path_str)
            
            if not os.path.exists(safe_path):
                # Check for files without extension or common issues
                return {"status": "error", "error": f"File not found: {path_str}"}
            
            if not os.path.isfile(safe_path):
                return {"status": "error", "error": f"Target is a directory, not a file: {path_str}"}

            with open(safe_path, "r", encoding="utf-8") as f:
                content = f.read()
                
            return {"status": "success", "data": {"content": content}}
        except Exception as e:
            return {"status": "error", "error": f"Read File Failed: {str(e)}"}

@register_node("write_file")
class WriteFileNode(FileBaseNode):
    """Writes content to a file within the sandbox. Creates directories if needed."""
    node_type = "write_file"
    inputs = {
        "file_path": {"type": "string", "description": "Path relative to sandbox root"},
        "content": {"type": "string", "description": "Text content to write"}
    }
    outputs = {
        "success": {"type": "boolean"},
        "path": {"type": "string"},
        "status": {"type": "string"}
    }

    async def execute(self, input_data: Any, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        try:
            path_str = self.get_config("file_path")
            content = self.get_config("content") or (input_data if isinstance(input_data, str) else "")
            
            if not path_str:
                return {"status": "error", "error": "File path is required."}
                
            safe_path = self._get_safe_path(path_str)
            
            # Ensure parent directories exist
            os.makedirs(os.path.dirname(safe_path), exist_ok=True)
            
            with open(safe_path, "w", encoding="utf-8") as f:
                f.write(content)
                
            return {"status": "success", "data": {"success": True, "path": path_str}}
        except Exception as e:
            return {"status": "error", "error": f"Write File Failed: {str(e)}"}

@register_node("delete_file")
class DeleteFileNode(FileBaseNode):
    """Deletes a file within the sandbox."""
    node_type = "delete_file"
    inputs = {
        "file_path": {"type": "string"}
    }
    outputs = {
      "success": {"type": "boolean"},
      "status": {"type": "string"}
    }
    async def execute(self, input_data: Any, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        try:
            path_str = self.get_config("file_path") or (input_data if isinstance(input_data, str) else "")
            if not path_str:
                 return {"status": "error", "error": "File path is required."}
            
            safe_path = self._get_safe_path(path_str)
            
            if os.path.exists(safe_path):
                if os.path.isdir(safe_path):
                    return {"status": "error", "error": "Cannot delete a directory using delete_file."}
                os.remove(safe_path)
                return {"status": "success", "data": {"success": True}}
            else:
                 return {"status": "error", "error": f"File not found: {path_str}"}
        except Exception as e:
            return {"status": "error", "error": f"Delete File Failed: {str(e)}"}
