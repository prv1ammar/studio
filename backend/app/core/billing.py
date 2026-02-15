from datetime import datetime
from typing import Dict, Any, Optional
from sqlmodel import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import async_session
from app.db.models import UsageRecord, Workspace, User
from app.core.tier_manager import tier_manager
import asyncio

class BillingManager:
    """
    Manages usage tracking, tier limits, and billing calculations.
    """
    
    async def get_or_create_usage(self, db: AsyncSession, workspace_id: str) -> UsageRecord:
        """Retrieves or initializes the usage record for the current month."""
        month = datetime.utcnow().strftime("%Y-%m")
        result = await db.execute(
            select(UsageRecord).where(
                UsageRecord.workspace_id == workspace_id,
                UsageRecord.month == month
            )
        )
        usage = result.scalar_one_or_none()
        
        if not usage:
            usage = UsageRecord(workspace_id=workspace_id, month=month)
            db.add(usage)
            try:
                await db.commit()
                await db.refresh(usage)
            except Exception:
                # Handle race condition if two nodes try to create at once
                await db.rollback()
                result = await db.execute(
                    select(UsageRecord).where(
                        UsageRecord.workspace_id == workspace_id,
                        UsageRecord.month == month
                    )
                )
                usage = result.scalar_one_or_none()
            
        return usage

    async def track_usage(self, workspace_id: str, tasks: int = 0, tokens: int = 0, cost: float = 0.0):
        """Asynchronously increments usage metrics for a workspace."""
        if not workspace_id:
            return
            
        async with async_session() as db:
            usage = await self.get_or_create_usage(db, workspace_id)
            usage.tasks_executed += tasks
            usage.ai_tokens_used += tokens
            usage.estimated_cost += cost
            usage.updated_at = datetime.utcnow()
            db.add(usage)
            await db.commit()

    async def check_limits(self, workspace_id: str) -> bool:
        """
        Verifies if a workspace is still within its monthly quota using TierManager.
        Returns True if allowed, False if limit exceeded.
        """
        if not workspace_id:
            return True
            
        async with async_session() as db:
            # 1. Fetch workspace to find owner
            res = await db.execute(select(Workspace).where(Workspace.id == workspace_id))
            workspace = res.scalar_one_or_none()
            if not workspace:
                return True
                
            # 2. Fetch owner to check their tier
            res = await db.execute(select(User).where(User.id == workspace.owner_id))
            owner = res.scalar_one_or_none()
            if not owner:
                return True
                
            tier = owner.tier or "free"
            
            # 3. Compare with current month's usage
            usage = await self.get_or_create_usage(db, workspace_id)
            
            # Check Task Limit
            task_limit = tier_manager.get_limit(tier, "max_tasks_per_month")
            if task_limit != -1 and usage.tasks_executed >= task_limit:
                print(f"⚠️ TASK LIMIT EXCEEDED: Workspace {workspace_id} ({usage.tasks_executed}/{task_limit})")
                return False
                
            # Check Token Limit
            token_limit = tier_manager.get_limit(tier, "max_tokens_per_month")
            if token_limit != -1 and usage.ai_tokens_used >= token_limit:
                print(f"⚠️ TOKEN LIMIT EXCEEDED: Workspace {workspace_id} ({usage.ai_tokens_used}/{token_limit})")
                return False
                
            return True

billing_manager = BillingManager()
