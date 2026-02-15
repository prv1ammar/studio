from fastapi import HTTPException, Depends, status
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select
from app.db.session import get_session
from app.db.models import WorkspaceMember, User
from app.api.auth import get_current_user

class PermissionChecker:
    def __init__(self, allowed_roles: List[str]):
        self.allowed_roles = allowed_roles

    async def __call__(
        self,
        workspace_id: str,
        current_user: User = Depends(get_current_user),
        db: AsyncSession = Depends(get_session)
    ):
        # 1. Check if user is a member of the workspace
        result = await db.execute(
            select(WorkspaceMember)
            .where(WorkspaceMember.workspace_id == workspace_id, WorkspaceMember.user_id == current_user.id)
        )
        member = result.scalar_one_or_none()

        if not member:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You are not a member of this workspace"
            )

        # 2. Check if user's role is allowed
        if member.role not in self.allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficent permissions. Required roles: {', '.join(self.allowed_roles)}"
            )

        return member

# Predefined deps
requires_viewer = PermissionChecker(["owner", "admin", "editor", "viewer", "guest"])
requires_editor = PermissionChecker(["owner", "admin", "editor"])
requires_admin = PermissionChecker(["owner", "admin"])
requires_owner = PermissionChecker(["owner"])
