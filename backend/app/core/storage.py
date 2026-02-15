import os
import uuid
import json
import fsspec
from typing import Any, Union, Dict
from app.core.config import settings

class StorageManager:
    """
    Handles persistence of large node outputs to prevent memory overflow.
    Supports local filesystem by default, but ready for S3/Minio via fsspec.
    """
    def __init__(self, storage_path: str = "outputs/refs"):
        self.storage_path = storage_path
        os.makedirs(self.storage_path, exist_ok=True)
        # Using local protocol, but can be s3:// etc.
        self.fs = fsspec.filesystem("file")

    def store(self, data: Any, filename: str = None) -> str:
        """
        Stores data and returns a reference string (URI).
        """
        if filename is None:
            filename = f"{uuid.uuid4()}.json"
        
        full_path = os.path.join(self.storage_path, filename)
        
        with self.fs.open(full_path, "w") as f:
            if isinstance(data, (dict, list)):
                json.dump(data, f)
            else:
                f.write(str(data))
        
        return f"ref://{filename}"

    def retrieve(self, reference: str) -> Any:
        """
        Retrieves data from a reference string.
        """
        if not reference.startswith("ref://"):
            return reference
            
        filename = reference.replace("ref://", "")
        full_path = os.path.join(self.storage_path, filename)
        
        if not self.fs.exists(full_path):
            raise FileNotFoundError(f"Storage reference {reference} not found.")
            
        with self.fs.open(full_path, "r") as f:
            content = f.read()
            try:
                return json.loads(content)
            except:
                return content

    def is_reference(self, data: Any) -> bool:
        return isinstance(data, str) and data.startswith("ref://")

storage_manager = StorageManager()

