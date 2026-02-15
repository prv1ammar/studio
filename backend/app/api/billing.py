from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_session
from app.db.models import User
from app.api.auth import get_current_user
from app.core.tier_manager import tier_manager

router = APIRouter()

@router.get("/plans")
async def get_plans(current_user: User = Depends(get_current_user)):
    """Get available subscription plans and comparison."""
    return tier_manager.compare_tiers()

@router.get("/subscription")
async def get_subscription(current_user: User = Depends(get_current_user)):
    """Get current user subscription details."""
    
    tier_info = tier_manager.get_tier_info(current_user.tier)
    
    return {
        "tier": current_user.tier,
        "status": current_user.subscription_status,
        "limits": tier_info["limits"],
        "features": tier_info["features"],
        "billing_email": current_user.billing_email,
        "ends_at": current_user.subscription_ends_at
    }

@router.post("/upgrade")
async def upgrade_subscription(tier: str, db: AsyncSession = Depends(get_session), current_user: User = Depends(get_current_user)):
    """
    Mock endpoint to upgrade subscription.
    In production, this would integrate with Stripe.
    """
    if tier not in tier_manager.TIERS:
        raise HTTPException(status_code=400, detail="Invalid tier")
    
    # Update user tier
    current_user.tier = tier
    current_user.subscription_status = "active"
    db.add(current_user)
    await db.commit()
    
    return {
        "status": "success",
        "message": f"Upgraded to {tier.capitalize()} plan",
        "tier": tier
    }

@router.get("/usage/{workspace_id}")
async def get_usage(workspace_id: str, db: AsyncSession = Depends(get_session), current_user: User = Depends(get_current_user)):
    """Retrieve usage statistics for a workspace."""
    from app.core.billing import billing_manager
    from app.core.tier_manager import tier_manager
    from app.db.models import Workspace
    
    # 1. Fetch workspace & owner
    res = await db.execute(select(Workspace).where(Workspace.id == workspace_id))
    workspace = res.scalar_one_or_none()
    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found")

    res = await db.execute(select(User).where(User.id == workspace.owner_id))
    owner = res.scalar_one_or_none()
    if not owner:
        raise HTTPException(status_code=404, detail="Owner not found")

    # 2. Get current month usage
    usage = await billing_manager.get_or_create_usage(db, workspace_id)
    
    # 3. Get limits
    tier_info = tier_manager.get_tier_info(owner.tier)
    
    return {
        "month": usage.month,
        "tasks_executed": usage.tasks_executed,
        "ai_tokens_used": usage.ai_tokens_used,
        "estimated_cost": usage.estimated_cost,
        "task_limit": tier_info["limits"].get("max_tasks_per_month", 0),
        "token_limit": tier_info["limits"].get("max_tokens_per_month", 0),
        "tier": owner.tier
    }
