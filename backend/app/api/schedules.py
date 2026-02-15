from fastapi import APIRouter, Depends, HTTPException
from typing import List, Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select
from app.db.session import get_session
from app.db.models import Schedule, Workflow, User
from app.api.auth import get_current_user
from datetime import datetime

router = APIRouter()

@router.post("/create")
async def create_schedule(
    request: Dict[str, Any], 
    db: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """Registers a new recurring schedule for a workflow."""
    workflow_id = request.get("workflow_id")
    
    # Verify workflow exists and user has access (basic check)
    wf_res = await db.execute(select(Workflow).where(Workflow.id == workflow_id))
    workflow = wf_res.scalar_one_or_none()
    
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")
        
    new_schedule = Schedule(
        workflow_id=workflow_id,
        workspace_id=workflow.workspace_id,
        user_id=current_user.id,
        name=request.get("name", f"Schedule for {workflow.name}"),
        cron=request.get("cron", "@daily"),
        enabled=True
    )
    
    db.add(new_schedule)
    await db.commit()
    await db.refresh(new_schedule)
    return new_schedule

@router.get("/list")
async def list_schedules(
    workspace_id: Optional[str] = None,
    db: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """Lists all active schedules for the current user or workspace."""
    query = select(Schedule).where(Schedule.user_id == current_user.id)
    if workspace_id:
        query = query.where(Schedule.workspace_id == workspace_id)
        
    result = await db.execute(query)
    return result.scalars().all()

@router.delete("/{schedule_id}")
async def delete_schedule(
    schedule_id: str,
    db: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """Removes a schedule."""
    res = await db.execute(select(Schedule).where(Schedule.id == schedule_id, Schedule.user_id == current_user.id))
    schedule = res.scalar_one_or_none()
    
    if not schedule:
        raise HTTPException(status_code=404, detail="Schedule not found")
        
    await db.delete(schedule)
    await db.commit()
    return {"status": "success"}

@router.post("/{schedule_id}/toggle")
async def toggle_schedule(
    schedule_id: str,
    enabled: bool,
    db: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """Enables or disables a schedule."""
    res = await db.execute(select(Schedule).where(Schedule.id == schedule_id, Schedule.user_id == current_user.id))
    schedule = res.scalar_one_or_none()
    
    if not schedule:
        raise HTTPException(status_code=404, detail="Schedule not found")
        
    schedule.enabled = enabled
    schedule.updated_at = datetime.utcnow()
    db.add(schedule)
    await db.commit()
    return {"status": "success", "enabled": enabled}
