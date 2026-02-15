"""
Binary Data Node - Studio Standard (Universal Method)
Batch 111: Utilities & Data Processing
"""
from typing import Any, Dict, Optional
import base64
import mimetypes
from ...base import BaseNode
from ...registry import register_node

@register_node("binary_data_node")
class BinaryDataNode(BaseNode):
    """
    Handle binary data: Base64, MIMEs, File Metadata.
    """
    node_type = "binary_data_node"
    version = "1.0.0"
    category = "utilities"
    credentials_required = []

    inputs = {
        "action": {
            "type": "dropdown",
            "default": "get_file_metadata",
            "options": ["get_file_metadata", "base64_encode", "base64_decode", "guess_mime_type"],
            "description": "Binary Data action"
        },
        "filename": {
            "type": "string",
            "optional": True
        },
        "content": {
            "type": "string",
            "optional": True
        }
    }

    outputs = {
        "result": {"type": "any"},
        "status": {"type": "string"}
    }

    async def execute(self, input_data: Any, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        try:
            action = self.get_config("action", "get_file_metadata")
            filename = self.get_config("filename", "file.bin")
            content = self.get_config("content")
            
            if action == "get_file_metadata":
                mime, encoding = mimetypes.guess_type(filename)
                size = len(content) if content else 0
                return {"status": "success", "data": {"filename": filename, "mime_type": mime, "encoding": encoding, "size": size}}

            elif action == "base64_encode":
                if not content: return {"status": "error", "error": "content required"}
                b = base64.b64encode(content.encode('utf-8')).decode('utf-8')
                return {"status": "success", "data": {"result": b}}

            elif action == "base64_decode":
                if not content: return {"status": "error", "error": "content required"}
                try:
                    s = base64.b64decode(content).decode('utf-8')
                    return {"status": "success", "data": {"result": s}}
                except:
                    return {"status": "error", "error": "Base64 decode failed"}

            elif action == "guess_mime_type":
                mime, _ = mimetypes.guess_type(filename)
                return {"status": "success", "data": {"mime_type": mime}}

            return {"status": "error", "error": f"Unsupported action: {action}"}

        except Exception as e:
            return {"status": "error", "error": f"Binary Data Node Failed: {str(e)}"}
