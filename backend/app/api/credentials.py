from fastapi import APIRouter, Depends, HTTPException, Body
from typing import List, Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select
from app.db.session import get_session
from app.db.models import Credential, User, WorkspaceMember
from app.api.auth import get_current_user
from app.core.credentials import cred_manager
import uuid

router = APIRouter()

@router.get("/list")
async def list_credentials(
    workspace_id: Optional[str] = None,
    db: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """Lists credentials metadata for the current user or workspace."""
    try:
        # If no workspace_id provided, default to user's personal ones or a default workspace
        # For simplicity in V1, we list all credentials the user has access to
        creds = await cred_manager.list_credentials(user_id=current_user.id, workspace_id=workspace_id)
        # Format for React Select (label/value)
        return {"credentials": [{"label": c["name"], "value": c["id"], "type": c["type"]} for c in creds]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/add")
async def add_credential(
    payload: Dict[str, Any] = Body(...),
    db: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """Securely adds a new encrypted credential."""
    try:
        cred_id = payload.get("id") or str(uuid.uuid4())
        cred_type = payload.get("type", "generic")
        name = payload.get("name", "Untitled")
        data = payload.get("data", {})
        workspace_id = payload.get("workspace_id")

        new_id = await cred_manager.add_credential(
            user_id=current_user.id,
            cred_type=cred_type,
            data=data,
            name=name,
            cred_id=cred_id,
            workspace_id=workspace_id
        )
        return {"status": "success", "id": new_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{cred_id}")
async def delete_credential(
    cred_id: str,
    db: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """Removes a credential."""
    try:
        success = await cred_manager.remove_credential(cred_id=cred_id, user_id=current_user.id)
        if not success:
            raise HTTPException(status_code=404, detail="Credential not found or permission denied")
        return {"status": "success"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{cred_id}/test")
async def test_credential(
    cred_id: str,
    db: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """
    Tests a credential's connectivity.
    Currently a stub that verifies decryption, but will soon call node-specific test methods.
    """
    try:
        cred_data = await cred_manager.get_credential(cred_id, user_id=current_user.id)
        if not cred_data:
            raise HTTPException(status_code=404, detail="Credential not found or decryption failed")
        
        # TODO: Implement Node-specific connection checks here 
        # For now, if we can decrypt it, we consider it "connected" for the UI.
        
        return {"status": "success", "message": f"Successfully validated encryption for '{cred_data['name']}'"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Connection Test Failed: {str(e)}")
