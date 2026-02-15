from fastapi import APIRouter, Depends, HTTPException
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select, desc
from app.db.session import get_session
from app.db.models import AuditLog, User, WorkspaceMember
from app.api.auth import get_current_user
from app.api.rbac import requires_admin

router = APIRouter()

@router.get("/list/{workspace_id}")
async def get_workspace_audit_logs(
    workspace_id: str,
    action_filter: Optional[str] = None,
    limit: int = 50,
    db: AsyncSession = Depends(get_session),
    member: WorkspaceMember = Depends(requires_admin) # Only admins/owners see logs
):
    """
    Returns recent audit logs for a workspace.
    Restricted to Admins and Owners.
    """
    query = select(AuditLog).where(AuditLog.workspace_id == workspace_id)
    
    if action_filter:
        query = query.where(AuditLog.action.ilike(f"%{action_filter}%"))
        
    query = query.order_by(desc(AuditLog.timestamp)).limit(limit)
    
    result = await db.execute(query)
    logs = result.scalars().all()
    
    # Enrich with user details if needed (for now just returning raw logs)
    return logs
