from fastapi import APIRouter, Depends, HTTPException, Body
from typing import List, Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select
from app.db.session import get_session
from app.db.models import Credential, User, WorkspaceMember
from app.api.auth import get_current_user
from app.api.rbac import requires_viewer, requires_editor
from app.core.credentials import cred_manager
from app.core.audit import audit_logger
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
        # Security: Validation
        if workspace_id:
            # Check if user is a member (Viewer+)
            res = await db.execute(select(WorkspaceMember).where(
                WorkspaceMember.workspace_id == workspace_id,
                WorkspaceMember.user_id == current_user.id
            ))
            if not res.scalar_one_or_none():
                raise HTTPException(status_code=403, detail="Access denied to this workspace")

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

        if workspace_id:
             # Check if user is Editor+
            res = await db.execute(select(WorkspaceMember).where(
                WorkspaceMember.workspace_id == workspace_id,
                WorkspaceMember.user_id == current_user.id
            ))
            member = res.scalar_one_or_none()
            if not member or member.role not in ["owner", "admin", "editor"]:
                raise HTTPException(status_code=403, detail="Insufficient permissions (Editor required)")

        new_id = await cred_manager.add_credential(
            user_id=current_user.id,
            cred_type=cred_type,
            data=data,
            name=name,
            cred_id=cred_id,
            workspace_id=workspace_id
        )

        # Audit Log
        await audit_logger.log(
            action="credential_create",
            user_id=current_user.id,
            workspace_id=workspace_id,
            details={"name": name, "type": cred_type, "cred_id": new_id}
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
        # 1. Fetch credential to check ownership/workspace
        res = await db.execute(select(Credential).where(Credential.id == cred_id))
        cred = res.scalar_one_or_none()
        if not cred:
            raise HTTPException(status_code=404, detail="Credential not found")
            
        # 2. Check Permissions
        if cred.workspace_id:
            # Check workspace membership (Editor+)
            res = await db.execute(select(WorkspaceMember).where(
                WorkspaceMember.workspace_id == cred.workspace_id,
                WorkspaceMember.user_id == current_user.id
            ))
            member = res.scalar_one_or_none()
            if not member or member.role not in ["owner", "admin", "editor"]:
                raise HTTPException(status_code=403, detail="Insufficient permissions to delete credential")
            
            # Use remove logic with workspace_id to ensure it finds it
            await cred_manager.remove_credential(cred_id=cred_id, user_id=current_user.id, workspace_id=cred.workspace_id)
        else:
            # Personal credential
            if cred.user_id != current_user.id:
                raise HTTPException(status_code=403, detail="Cannot delete another user's private credential")
            await cred_manager.remove_credential(cred_id=cred_id, user_id=current_user.id)

        # Audit Log
        await audit_logger.log(
            action="credential_delete",
            user_id=current_user.id,
            workspace_id=cred.workspace_id,
            details={"name": cred.name, "type": cred.type, "cred_id": cred_id}
        )

        return {"status": "success"}
    except HTTPException as e:
        raise e
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
