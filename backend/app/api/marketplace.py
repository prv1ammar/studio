from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select, or_, col
from app.db.session import get_session
from app.db.models import Template, Workflow, User, WorkspaceMember
from app.api.auth import get_current_user
from datetime import datetime
import uuid

router = APIRouter()

@router.get("/")
async def list_market_templates(
    category: Optional[str] = None,
    search: Optional[str] = None,
    db: AsyncSession = Depends(get_session)
):
    """Lists all public templates with optional filtering."""
    query = select(Template).where(Template.is_public == True)
    
    if category:
        query = query.where(Template.category == category)
    if search:
        query = query.where(or_(
            Template.name.contains(search),
            Template.description.contains(search)
        ))
        
    res = await db.execute(query.order_by(Template.downloads_count.desc()))
    return res.scalars().all()

@router.post("/publish")
async def publish_as_template(
    workflow_id: str,
    description: str,
    category: str = "Generic",
    tags: List[str] = [],
    db: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """Publishes an existing workflow as a public Marketplace template."""
    res = await db.execute(select(Workflow).where(Workflow.id == workflow_id))
    workflow = res.scalar_one_or_none()
    
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")
        
    # Check permissions (Owner/Admin only)
    perm_res = await db.execute(select(WorkspaceMember).where(
        WorkspaceMember.workspace_id == workflow.workspace_id,
        WorkspaceMember.user_id == current_user.id
    ))
    membership = perm_res.scalar_one_or_none()
    if not membership or membership.role not in ["owner", "admin"]:
        raise HTTPException(status_code=403, detail="Only workspace owners/admins can publish templates")

    new_template = Template(
        name=workflow.name,
        description=description,
        category=category,
        tags=tags,
        definition=workflow.definition,
        author_id=current_user.id,
        workspace_id=workflow.workspace_id,
        is_public=True
    )
    
    db.add(new_template)
    await db.commit()
    return new_template

@router.post("/{template_id}/clone")
async def clone_template(
    template_id: str,
    target_workspace_id: str,
    db: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """Clones a marketplace template into a local workspace as a new workflow."""
    res = await db.execute(select(Template).where(Template.id == template_id))
    template = res.scalar_one_or_none()
    
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")

    # Check target workspace access
    perm_res = await db.execute(select(WorkspaceMember).where(
        WorkspaceMember.workspace_id == target_workspace_id,
        WorkspaceMember.user_id == current_user.id
    ))
    if not perm_res.scalar_one_or_none():
        raise HTTPException(status_code=403, detail="Access denied to target workspace")

    # Create new workflow from template
    new_workflow = Workflow(
        name=f"{template.name} (Cloned)",
        workspace_id=target_workspace_id,
        definition=template.definition
    )
    
    # Increment download count
    template.downloads_count += 1
    db.add(template)
    db.add(new_workflow)
    
    await db.commit()
    return {"status": "success", "workflow_id": new_workflow.id}
