from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Optional, Dict, Any
from sqlmodel import select, desc
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_session
from app.db.models import Template, User, Workflow, WorkspaceMember
from app.api.auth import get_current_user
import uuid

router = APIRouter()

@router.get("/list", response_model=List[Template])
async def list_templates(
    category: Optional[str] = None,
    public_only: bool = True,
    db: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """
    Lists available templates. Public templates are visible to everyone.
    Private templates are visible only within their workspace.
    """
    query = select(Template)
    
    if public_only:
        query = query.where(Template.is_public == True)
    else:
        # Show public templates OR private ones the user has access to (not implemented fully yet, default to public)
        query = query.where(Template.is_public == True)
        
    if category:
        query = query.where(Template.category == category)
        
    query = query.order_by(desc(Template.downloads_count))
    
    result = await db.execute(query)
    templates = result.scalars().all()
    return templates

@router.get("/{template_id}", response_model=Template)
async def get_template_details(
    template_id: str,
    db: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """Retrieves full details of a specific template."""
    result = await db.execute(select(Template).where(Template.id == template_id))
    template = result.scalar_one_or_none()
    
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
        
    if not template.is_public:
        # Check workspace access (place holder for private templates)
        pass
        
    return template

@router.post("/clone/{template_id}")
async def clone_template_to_workspace(
    template_id: str,
    workspace_id: str,
    db: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """
    Clones a template into a specific workspace as a new workflow.
    """
    # 1. Fetch template
    res = await db.execute(select(Template).where(Template.id == template_id))
    template = res.scalar_one_or_none()
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")

    # 2. Verify workspace access
    res = await db.execute(select(WorkspaceMember).where(
        WorkspaceMember.workspace_id == workspace_id,
        WorkspaceMember.user_id == current_user.id
    ))
    membership = res.scalar_one_or_none()
    if not membership or membership.role == "viewer":
        raise HTTPException(status_code=403, detail="Insufficient permissions in target workspace")

    # 3. Create new workflow from template
    new_workflow = Workflow(
        name=f"Copy of {template.name}",
        description=template.description,
        definition=template.definition,
        workspace_id=workspace_id
    )
    
    db.add(new_workflow)
    
    # 4. Increment download count
    template.downloads_count += 1
    db.add(template)
    
    await db.commit()
    await db.refresh(new_workflow)
    
    return {
        "status": "success",
        "workflow_id": new_workflow.id,
        "definition": new_workflow.definition,
        "name": new_workflow.name,
        "message": f"Successfully cloned '{template.name}'"
    }
