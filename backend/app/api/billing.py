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
