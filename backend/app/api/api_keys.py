from fastapi import APIRouter, Depends, HTTPException, Header, Body
from typing import List, Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select
from app.db.session import get_session
from app.db.models import ApiKey, User, Workflow, WorkspaceMember
from app.api.auth import get_current_user
from app.core.engine import engine
from datetime import datetime
import secrets
import hashlib
import uuid
import json

router = APIRouter()

def generate_api_key():
    """Generates a secure API key with prefix."""
    token = secrets.token_urlsafe(32)
    key = f"st_live_{token}"
    key_hash = hashlib.sha256(key.encode()).hexdigest()
    return key, key_hash, key[:12]

@router.post("/generate")
async def create_api_key(
    name: str = Body(..., embed=True),
    workspace_id: str = Body(..., embed=True),
    db: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """
    Generates a new API Key for programmatic access.
    The raw key is returned ONLY once.
    """
    # 1. Verify access
    res = await db.execute(select(WorkspaceMember).where(
        WorkspaceMember.workspace_id == workspace_id, 
        WorkspaceMember.user_id == current_user.id
    ))
    if not res.scalar_one_or_none():
        raise HTTPException(status_code=403, detail="Access denied to this workspace")

    # 2. Generate Key
    raw_key, key_hash, prefix = generate_api_key()
    
    new_key = ApiKey(
        workspace_id=workspace_id,
        user_id=current_user.id,
        name=name,
        key_hash=key_hash,
        key_prefix=prefix,
        scopes=["workflow:run"],
        enabled=True
    )
    
    db.add(new_key)
    await db.commit()
    
    return {
        "id": new_key.id,
        "name": new_key.name,
        "api_key": raw_key, # THE ONLY TIME THIS IS RETURNED
        "message": "Store this key securely. It will not be shown again."
    }

@router.get("/list/{workspace_id}")
async def list_keys(
    workspace_id: str,
    db: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """Lists metadata for all API keys in a workspace."""
    res = await db.execute(select(ApiKey).where(ApiKey.workspace_id == workspace_id))
    keys = res.scalars().all()
    # Mask sensitivity
    return [{"id": k.id, "name": k.name, "prefix": k.key_prefix, "created_at": k.created_at, "last_used": k.last_run_at} for k in keys]

@router.post("/v1/trigger/{workflow_id}")
async def trigger_workflow(
    workflow_id: str,
    payload: Dict[str, Any] = Body(...),
    x_api_key: str = Header(...),
    db: AsyncSession = Depends(get_session)
):
    """
    PROGRAMMATIC TRIGGER ENDPOINT.
    Allows external systems to trigger Studio workflows using an API Key.
    """
    # 1. Authenticate via Key Hash
    key_hash = hashlib.sha256(x_api_key.encode()).hexdigest()
    res = await db.execute(select(ApiKey).where(ApiKey.key_hash == key_hash, ApiKey.enabled == True))
    api_key_obj = res.scalar_one_or_none()
    
    if not api_key_obj:
        raise HTTPException(status_code=401, detail="Invalid or disabled API Key")

    # 2. Verify Workflow Access
    wf_res = await db.execute(select(Workflow).where(Workflow.id == workflow_id, Workflow.workspace_id == api_key_obj.workspace_id))
    workflow = wf_res.scalar_one_or_none()
    
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found in the key's workspace")

    # 3. Trigger via Engine
    execution_id = str(uuid.uuid4())
    
    import asyncio
    asyncio.create_task(
        engine.process_workflow(
            workflow.definition,
            message=json.dumps(payload),
            context={
                "triggered_by": "api_key",
                "api_key_id": api_key_obj.id,
                "workspace_id": api_key_obj.workspace_id,
                "execution_id": execution_id
            }
        )
    )

    # 4. Update Usage
    api_key_obj.last_used_at = datetime.utcnow()
    db.add(api_key_obj)
    await db.commit()

    return {
        "status": "accepted",
        "execution_id": execution_id,
        "workflow": workflow.name
    }
