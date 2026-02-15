from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select, and_
from app.db.session import get_session
from app.db.models import User, Workspace, WorkspaceMember, Workflow, Comment
from app.api.auth import get_current_user
from app.api.rbac import requires_viewer, requires_editor, requires_admin, requires_owner
from pydantic import BaseModel
import uuid

router = APIRouter()

class WorkspaceCreate(BaseModel):
    name: str
    description: Optional[str] = None

class CommentCreate(BaseModel):
    workflow_id: str
    node_id: Optional[str] = None
    text: str

@router.get("/list", response_model=List[Workspace])
async def list_workspaces(
    db: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """Returns all workspaces the user is a member of."""
    result = await db.execute(
        select(Workspace)
        .join(WorkspaceMember)
        .where(WorkspaceMember.user_id == current_user.id)
    )
    return result.scalars().all()

@router.post("/create", response_model=Workspace)
async def create_workspace(
    ws_in: WorkspaceCreate,
    db: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """Creates a new workspace and adds the user as owner."""
    new_ws = Workspace(
        name=ws_in.name,
        description=ws_in.description,
        owner_id=current_user.id
    )
    db.add(new_ws)
    await db.flush()

    membership = WorkspaceMember(
        workspace_id=new_ws.id,
        user_id=current_user.id,
        role="owner"
    )
    db.add(membership)
    await db.commit()
    await db.refresh(new_ws)
    return new_ws

@router.get("/{workspace_id}/members")
async def get_workspace_members(
    workspace_id: str,
    db: AsyncSession = Depends(get_session),
    member: WorkspaceMember = Depends(requires_viewer)
):
    """Returns members of a workspace if user is a member."""
    result = await db.execute(
        select(User.id, User.email, User.full_name, WorkspaceMember.role)
        .join(WorkspaceMember, User.id == WorkspaceMember.user_id)
        .where(WorkspaceMember.workspace_id == workspace_id)
    )
    return [{"id": r[0], "email": r[1], "full_name": r[2], "role": r[3]} for r in result.all()]

@router.post("/{workspace_id}/invite")
async def invite_to_workspace(
    workspace_id: str,
    email: str,
    role: str = "editor",
    db: AsyncSession = Depends(get_session),
    member: WorkspaceMember = Depends(requires_editor)
):
    """Invites a user to a workspace by email."""
    # Find invited user
    user_result = await db.execute(select(User).where(User.email == email))
    invited_user = user_result.scalar_one_or_none()
    if not invited_user:
        raise HTTPException(status_code=404, detail="User not found")

    # Add to workspace
    new_member = WorkspaceMember(
        workspace_id=workspace_id,
        user_id=invited_user.id,
        role=role
    )
    db.add(new_member)
    try:
        await db.commit()
    except:
        await db.rollback()
        raise HTTPException(status_code=400, detail="User already a member")

    return {"status": "success", "message": f"User {email} added to workspace"}

# Comments API
@router.get("/workflows/{workflow_id}/comments", response_model=List[Dict[str, Any]])
async def get_comments(
    workflow_id: str,
    db: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """Retrieves all comments for a workflow."""
    result = await db.execute(
        select(Comment, User.full_name, User.email)
        .join(User, Comment.user_id == User.id)
        .where(Comment.workflow_id == workflow_id)
        .order_by(Comment.created_at.asc())
    )
    return [
        {
            **c[0].model_dump(),
            "user_name": c[1] or c[2],
        } for c in result.all()
    ]

@router.post("/workflows/comments", response_model=Comment)
async def create_comment(
    comment_in: CommentCreate,
    db: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """Creates a new comment on a workflow/node."""
    new_comment = Comment(
        workflow_id=comment_in.workflow_id,
        node_id=comment_in.node_id,
        user_id=current_user.id,
        text=comment_in.text
    )
    db.add(new_comment)
    await db.commit()
    await db.refresh(new_comment)
    return new_comment
