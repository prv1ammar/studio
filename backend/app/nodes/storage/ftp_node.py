"""
FTP/SFTP Node - Studio Standard (Universal Method)
Batch 107: Cloud Storage
"""
from typing import Any, Dict, Optional
import aiohttp
import ftplib
import io
from ...base import BaseNode
from ...registry import register_node

# Note: SFTP requires Paramiko or asyncssh. FTP is standard lib.
# For simplicity with available dependencies, implemented FTP first.
# SFTP would be a distinct implementation or require adding 'paramiko' to requirements.

@register_node("ftp_node")
class FTPNode(BaseNode):
    """
    FTP server integration for file transfer.
    """
    node_type = "ftp_node"
    version = "1.0.0"
    category = "storage"
    credentials_required = ["ftp_auth"]

    inputs = {
        "action": {
            "type": "dropdown",
            "default": "list_files",
            "options": ["list_files", "upload_file", "download_file", "delete_file"],
            "description": "FTP action"
        },
        "path": {
            "type": "string",
            "optional": True,
            "description": "Remote path"
        },
        "file_content": {
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
            creds = await self.get_credential("ftp_auth")
            host = creds.get("host")
            username = creds.get("username")
            password = creds.get("password")
            port = int(creds.get("port", 21))
            
            if not host or not username:
                return {"status": "error", "error": "FTP credentials required"}
            
            action = self.get_config("action", "list_files")
            path = self.get_config("path", "/")

            # FTP operations are blocking I/O in standard library.
            # In purely async app, run in executor.
            import asyncio
            loop = asyncio.get_event_loop()
            
            def ftp_task():
                ftp = ftplib.FTP()
                ftp.connect(host, port)
                ftp.login(username, password)
                
                try:
                    if action == "list_files":
                        files = []
                        ftp.cwd(path)
                        ftp.retrlines('LIST', files.append)
                        return files
                    
                    elif action == "upload_file":
                        file_content = self.get_config("file_content")
                        if file_content is None:
                            raise ValueError("file_content required")
                        
                        # Assuming text content for simplicity, or bytes if passed as such
                        # Provide string buffer
                        if isinstance(file_content, str):
                             bio = io.BytesIO(file_content.encode('utf-8'))
                        else:
                             bio = io.BytesIO(file_content)
                             
                        ftp.storbinary(f"STOR {path}", bio)
                        return "Upload successful"
                    
                    elif action == "download_file":
                        bio = io.BytesIO()
                        ftp.retrbinary(f"RETR {path}", bio.write)
                        return bio.getvalue().decode('utf-8', errors='ignore') # return string
                        
                    elif action == "delete_file":
                        ftp.delete(path)
                        return "File deleted"
                        
                finally:
                    ftp.quit()

            result = await loop.run_in_executor(None, ftp_task)
            return {"status": "success", "data": {"result": result}}

        except Exception as e:
            return {"status": "error", "error": f"FTP Node Failed: {str(e)}"}
