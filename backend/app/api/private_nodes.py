from fastapi import APIRouter, Depends, HTTPException, Body
from typing import List, Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select
from app.db.session import get_session
from app.db.models import PrivateNode, User, WorkspaceMember
from app.api.auth import get_current_user
from app.api.rbac import requires_viewer
from app.core.audit import audit_logger
from datetime import datetime
import uuid

router = APIRouter()

@router.post("/register")
async def register_private_node(
    data: Dict[str, Any] = Body(...),
    db: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """
    Registers a new custom private node for the workspace.
    Requires 'Admin' or 'Editor' role.
    """
    workspace_id = data.get("workspace_id")
    if not workspace_id:
        raise HTTPException(status_code=400, detail="workspace_id is required")

    # 1. Check Permissions
    res = await db.execute(select(WorkspaceMember).where(
        WorkspaceMember.workspace_id == workspace_id, 
        WorkspaceMember.user_id == current_user.id
    ))
    membership = res.scalar_one_or_none()
    if not membership or membership.role not in ["owner", "admin", "editor"]:
        raise HTTPException(status_code=403, detail="Insufficient permissions to register nodes")

    # 2. Check for duplicate node_type
    node_type = data.get("node_type")
    res = await db.execute(select(PrivateNode).where(PrivateNode.node_type == node_type))
    if res.scalar_one_or_none():
        raise HTTPException(status_code=400, detail=f"Node type '{node_type}' is already registered")

    # 3. Create Node
    new_node = PrivateNode(
        workspace_id=workspace_id,
        user_id=current_user.id,
        name=data.get("name"),
        node_type=node_type,
        category=data.get("category", "Custom"),
        description=data.get("description"),
        icon=data.get("icon", "Box"),
        color=data.get("color", "#94a3b8"),
        code=data.get("code"),
        ui_metadata=data.get("ui_metadata", {}),
        enabled=True
    )
    
    db.add(new_node)
    await db.commit()
    await db.refresh(new_node)
    
    # 4. Invalidate potentially cached failure in Registry
    from app.nodes.private_registry import PrivateRegistry
    PrivateRegistry.invalidate_cache(node_type, workspace_id)
    
    # Audit Log
    await audit_logger.log(
        action="private_node_register",
        user_id=current_user.id,
        workspace_id=workspace_id,
        details={"node_type": node_type, "name": new_node.name}
    )

    return new_node

@router.get("/list/{workspace_id}")
async def list_private_nodes(
    workspace_id: str,
    db: AsyncSession = Depends(get_session),
    member: WorkspaceMember = Depends(requires_viewer)
):
    """Lists all private nodes available in the specified workspace."""
    # Access verified by dependency
    res = await db.execute(select(PrivateNode).where(PrivateNode.workspace_id == workspace_id))
    return res.scalars().all()

@router.delete("/{node_id}")
async def delete_private_node(
    node_id: str,
    db: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """Removes a private node."""
    res = await db.execute(select(PrivateNode).where(PrivateNode.id == node_id))
    node = res.scalar_one_or_none()
    if not node:
        raise HTTPException(status_code=404, detail="Node not found")

    # Check Permissions
    perm_res = await db.execute(select(WorkspaceMember).where(
        WorkspaceMember.workspace_id == node.workspace_id, 
        WorkspaceMember.user_id == current_user.id
    ))
    membership = perm_res.scalar_one_or_none()
    if not membership or membership.role not in ["owner", "admin", "editor"]:
         raise HTTPException(status_code=403, detail="Insufficient permissions")

    # Invalidate cache before deleting
    from app.nodes.private_registry import PrivateRegistry
    PrivateRegistry.invalidate_cache(node.node_type, node.workspace_id)

    await db.delete(node)
    await db.commit()

    # Audit Log
    await audit_logger.log(
        action="private_node_delete",
        user_id=current_user.id,
        workspace_id=node.workspace_id,
        details={"node_type": node.node_type}
    )

    return {"status": "success"}
