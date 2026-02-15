import json
import os
import base64
from typing import Dict, Any, Optional, List
from pathlib import Path
from datetime import datetime
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from app.core.config import settings
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select
from app.db.models import Credential
from app.db.session import async_session

class CredentialStore:
    """
    Centralized store for managing service credentials with AES-256 GCM encryption.
    Transitioned to PostgreSQL-backed storage for Phase 3.
    """
    
    def __init__(self):
        # Initialize AES-256 GCM
        key_bytes = base64.urlsafe_b64decode(settings.ENCRYPTION_KEY)
        self.aesgcm = AESGCM(key_bytes)

    def _encrypt(self, data: str) -> str:
        nonce = os.urandom(12)
        ct = self.aesgcm.encrypt(nonce, data.encode(), None)
        return base64.b64encode(nonce + ct).decode()

    def _decrypt(self, encrypted_data: str) -> str:
        decoded = base64.b64decode(encrypted_data)
        nonce = decoded[:12]
        ct = decoded[12:]
        return self.aesgcm.decrypt(nonce, ct, None).decode()

    async def add_credential(self, user_id: str, cred_type: str, data: Dict[str, Any], name: str = "", cred_id: str = None, workspace_id: Optional[str] = None):
        """Adds a new encrypted credential to the database."""
        encrypted_payload = self._encrypt(json.dumps(data))
        
        async with async_session() as db:
            new_cred = Credential(
                id=cred_id,
                user_id=user_id,
                workspace_id=workspace_id,
                type=cred_type,
                name=name or f"{cred_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                encrypted_data=encrypted_payload
            )
            db.add(new_cred)
            await db.commit()
            await db.refresh(new_cred)
            return new_cred.id

    async def get_credential(self, cred_id: str, user_id: Optional[str] = None, workspace_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Retrieves and decrypts the full credential object."""
        async with async_session() as db:
            query = select(Credential).where(Credential.id == cred_id)
            if workspace_id:
                # If workspace is provided, anyone in workspace can use it
                # For simplicity, we just filter by workspace_id
                query = query.where(Credential.workspace_id == workspace_id)
            elif user_id:
                query = query.where(Credential.user_id == user_id)
            
            result = await db.execute(query)
            cred = result.scalar_one_or_none()
            
            if not cred:
                return None
            
            try:
                decrypted_json = self._decrypt(cred.encrypted_data)
                return {
                    "id": cred.id,
                    "type": cred.type,
                    "name": cred.name,
                    "data": json.loads(decrypted_json)
                }
            except Exception as e:
                print(f" Failed to decrypt credential {cred_id}: {e}")
                return None

    async def list_credentials(self, user_id: str, cred_type: str = None, workspace_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Lists metadata for all credentials for a specific user or workspace."""
        async with async_session() as db:
            from app.db.models import WorkspaceMember
            if workspace_id:
                # Get all credentials for this workspace
                query = select(Credential).where(Credential.workspace_id == workspace_id)
            else:
                # Get user's personal/global credentials
                query = select(Credential).where(Credential.user_id == user_id)
                
            if cred_type:
                query = query.where(Credential.type == cred_type)
            
            result = await db.execute(query)
            creds = result.scalars().all()
            
            return [
                {
                    "id": c.id,
                    "type": c.type,
                    "name": c.name
                } for c in creds
            ]

    async def remove_credential(self, cred_id: str, user_id: str, workspace_id: Optional[str] = None):
        """Removes a credential belonging to a specific user or workspace."""
        async with async_session() as db:
            query = select(Credential).where(Credential.id == cred_id)
            if workspace_id:
                query = query.where(Credential.workspace_id == workspace_id)
            else:
                query = query.where(Credential.user_id == user_id)

            result = await db.execute(query)
            cred = result.scalar_one_or_none()
            
            if cred:
                await db.delete(cred)
                await db.commit()
                return True
            return False

cred_manager = CredentialStore()

