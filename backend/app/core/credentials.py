import json
import os
from typing import Dict, Any, Optional, List
from pathlib import Path

class CredentialStore:
    """
    Centralized store for managing service credentials.
    In production, this should use encryption (e.g., Cryptography.fernet).
    """
    
    def __init__(self, storage_path: str = None):
        if storage_path is None:
            # Default to a hidden file in the project root or backend/data
            self.storage_path = Path("backend/data/credentials.json").absolute()
        else:
            self.storage_path = Path(storage_path)
            
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        self._ensure_file()

    def _ensure_file(self):
        if not self.storage_path.exists():
            with open(self.storage_path, 'w') as f:
                json.dump({}, f)

    def _load(self) -> Dict[str, Any]:
        with open(self.storage_path, 'r') as f:
            return json.load(f)

    def _save(self, data: Dict[str, Any]):
        with open(self.storage_path, 'w') as f:
            json.dump(data, f, indent=4)

    def add_credential(self, cred_id: str, cred_type: str, data: Dict[str, Any], name: str = ""):
        """
        Adds or updates a credential.
        :param cred_id: Unique identifier (e.g., 'google_main')
        :param cred_type: Category (e.g., 'google_oauth', 'openai_api_key')
        :param data: The actual sensitive data dictionary
        :param name: Friendly name for the UI
        """
        store = self._load()
        store[cred_id] = {
            "id": cred_id,
            "type": cred_type,
            "name": name or cred_id,
            "data": data,
            "created_at": str(os.path.getmtime(self.storage_path)) if self.storage_path.exists() else ""
        }
        self._save(store)
        return cred_id

    def get_credential(self, cred_id: str) -> Optional[Dict[str, Any]]:
        """Retrieves the full credential object."""
        store = self._load()
        return store.get(cred_id)

    def list_credentials(self, cred_type: str = None) -> List[Dict[str, Any]]:
        """Lists metadata for all credentials (excluding data for security if requested)."""
        store = self._load()
        creds = list(store.values())
        if cred_type:
            creds = [c for c in creds if c["type"] == cred_type]
        
        # Strip the 'data' for listing if needed, but for runtime injection we need it.
        return creds

    def remove_credential(self, cred_id: str):
        store = self._load()
        if cred_id in store:
            del store[cred_id]
            self._save(store)
            return True
        return False

# Singleton instance
cred_manager = CredentialStore()
