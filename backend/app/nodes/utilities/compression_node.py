"""
Compression Node - Studio Standard (Universal Method)
Batch 111: Utilities & Data Processing
"""
from typing import Any, Dict, Optional
import gzip
import zipfile
import io
from ..base import BaseNode
from ..registry import register_node

@register_node("compression_node")
class CompressionNode(BaseNode):
    """
    Compress or Decompress files/data (GZIP, ZIP).
    """
    node_type = "compression_node"
    version = "1.0.0"
    category = "utilities"
    credentials_required = []


    properties = [
        {
            'displayName': 'Operation',
            'name': 'operation',
            'type': 'options',
            'default': 'compress',
            'options': [
                {'name': 'Compress', 'value': 'compress'},
                {'name': 'Decompress', 'value': 'decompress'},
            ],
            'description': 'Compression action',
        },
        {
            'displayName': 'Content',
            'name': 'content',
            'type': 'string',
            'default': '',
            'description': 'Content to process',
        },
        {
            'displayName': 'Filename',
            'name': 'filename',
            'type': 'string',
            'default': '',
            'description': 'Filename inside archive',
        },
        {
            'displayName': 'Format',
            'name': 'format',
            'type': 'options',
            'default': 'gzip',
            'options': [
                {'name': 'Gzip', 'value': 'gzip'},
                {'name': 'Zip', 'value': 'zip'},
            ],
        },
    ]
    inputs = {
        "action": {
            "type": "dropdown",
            "default": "compress",
            "options": ["compress", "decompress"],
            "description": "Compression action"
        },
        "format": {
            "type": "dropdown",
            "default": "gzip",
            "options": ["gzip", "zip"],
            "optional": True
        },
        "content": {
            "type": "string",
            "optional": True,
            "description": "Content to process"
        },
        "filename": {
            "type": "string",
            "optional": True,
            "description": "Filename inside archive"
        }
    }

    outputs = {
        "result": {"type": "any"},
        "status": {"type": "string"}
    }

    async def execute(self, input_data: Any, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        try:
            content = self.get_config("content")
            if content is None: content = str(input_data)
            
            format = self.get_config("format", "gzip")
            action = self.get_config("action", "compress")
            filename = self.get_config("filename", "file.txt")
            
            if action == "compress":
                if format == "gzip":
                    # Compress string to gzip bytes
                    out = io.BytesIO()
                    with gzip.GzipFile(fileobj=out, mode="w") as f:
                        f.write(content.encode('utf-8'))
                    return {"status": "success", "data": {"result": out.getvalue()}} # Returns bytes
                
                elif format == "zip":
                    out = io.BytesIO()
                    with zipfile.ZipFile(out, mode="w", compression=zipfile.ZIP_DEFLATED) as zf:
                        zf.writestr(filename, content)
                    return {"status": "success", "data": {"result": out.getvalue()}}

            elif action == "decompress":
                # Input must be bytes or emulate it
                # Assuming input comes as bytes or base64 decoded string
                if isinstance(content, str):
                    # Try to handle if it's raw string? usually binary is handled differently in Studio context
                    # If passed as "string" here, assume it's bytes if possible or encoded
                    # For simplicity, if string, encode back to bytes to try decompressing?
                    # Or fail if not bytes.
                    c_bytes = content.encode('utf-8') # Likely wrong if it's already binary data represented as string
                    # But if it's Base64 string passed, decode first?
                    # Let's assume input is bytes if passed correctly from specialized upstream node.
                    # Fallback:
                    c_bytes = content.encode('latin1') # Common trick for raw bytes in str
                else:
                    c_bytes = content

                if format == "gzip":
                    try:
                        with gzip.GzipFile(fileobj=io.BytesIO(c_bytes), mode="r") as f:
                            res = f.read().decode('utf-8')
                        return {"status": "success", "data": {"result": res}}
                    except:
                        return {"status": "error", "error": "Gzip Decompression Failed"}

                elif format == "zip":
                    try:
                        with zipfile.ZipFile(io.BytesIO(c_bytes)) as zf:
                            # Extract first file text
                            first_file = zf.namelist()[0]
                            res = zf.read(first_file).decode('utf-8')
                        return {"status": "success", "data": {"result": res}}
                    except:
                        return {"status": "error", "error": "Zip Decompression Failed"}

            return {"status": "error", "error": f"Unsupported action: {action}"}

        except Exception as e:
            return {"status": "error", "error": f"Compression Node Failed: {str(e)}"}