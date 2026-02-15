import redis.asyncio as aioredis
from typing import Optional
from app.core.config import settings
import time

class RateLimiter:
    """
    Redis-backed rate limiter for execution control.
    Prevents abuse and ensures fair resource allocation across users/workspaces.
    """
    
    def __init__(self):
        self.redis: Optional[aioredis.Redis] = None
    
    async def init_redis(self, redis_client: aioredis.Redis):
        """Initialize with the app's Redis instance."""
        self.redis = redis_client
    
    async def check_user_limit(self, user_id: str, tier: str = "free", custom_limits: Optional[dict] = None) -> bool:
        """
        Check if user has exceeded tier-based concurrent execution limit.
        Returns True if allowed, False if limit exceeded.
        """
        if not self.redis:
            return True  # Fail open if Redis unavailable
        
        from app.core.tier_manager import tier_manager
        
        limit = tier_manager.get_concurrent_job_limit(tier, custom_limits)
        
        # -1 means unlimited
        if limit == -1:
            return True
            
        key = f"rate_limit:user:{user_id}:concurrent"
        current_count = await self.redis.get(key)
        
        if current_count and int(current_count) >= limit:
            return False
        
        return True
    
    async def check_workspace_limit(self, workspace_id: str, tier: str = "free", custom_limits: Optional[dict] = None) -> bool:
        """
        Check if workspace has exceeded tier-based concurrent execution limit.
        Returns True if allowed, False if limit exceeded.
        """
        if not self.redis:
            return True
            
        from app.core.tier_manager import tier_manager
        
        # Workspace limits often match user limits or have a multiplier
        # For now, we'll use the same limit logic, potentially configurable per tier
        limit = tier_manager.get_limit(tier, "max_concurrent_jobs")
        # You might want a separate workspace limit in TierManager later
        
        if limit == -1:
            return True
        
        key = f"rate_limit:workspace:{workspace_id}:concurrent"
        current_count = await self.redis.get(key)
        
        if current_count and int(current_count) >= limit: # Using same limit for now, or settings.MAX_CONCURRENT_JOBS_PER_WORKSPACE if distinct
             # Fallback to settings if needed, but aim for tier-based
             # Let's trust TierManager. If we want workspace specific, we add it there.
             # For legacy support, maybe check if limit is very low?
             return False
        
        return True
    
    async def acquire(self, user_id: str, workspace_id: Optional[str] = None, execution_id: str = None):
        """
        Acquire a rate limit slot for execution.
        Increments counters for user and workspace.
        """
        if not self.redis:
            return
        
        user_key = f"rate_limit:user:{user_id}:concurrent"
        await self.redis.incr(user_key)
        await self.redis.expire(user_key, settings.WORKFLOW_TIMEOUT)
        
        if workspace_id:
            ws_key = f"rate_limit:workspace:{workspace_id}:concurrent"
            await self.redis.incr(ws_key)
            await self.redis.expire(ws_key, settings.WORKFLOW_TIMEOUT)
        
        # Track execution for cleanup
        if execution_id:
            exec_key = f"execution:{execution_id}:limits"
            await self.redis.setex(
                exec_key, 
                settings.WORKFLOW_TIMEOUT,
                f"{user_id}:{workspace_id or 'none'}"
            )
    
    async def release(self, user_id: str, workspace_id: Optional[str] = None):
        """
        Release a rate limit slot after execution completes.
        Decrements counters for user and workspace.
        """
        if not self.redis:
            return
        
        user_key = f"rate_limit:user:{user_id}:concurrent"
        current = await self.redis.get(user_key)
        if current and int(current) > 0:
            await self.redis.decr(user_key)
        
        if workspace_id:
            ws_key = f"rate_limit:workspace:{workspace_id}:concurrent"
            current = await self.redis.get(ws_key)
            if current and int(current) > 0:
                await self.redis.decr(ws_key)
    
    async def get_current_usage(self, user_id: str, workspace_id: Optional[str] = None) -> dict:
        """Get current usage stats for monitoring."""
        if not self.redis:
            return {"user": 0, "workspace": 0}
        
        user_count = await self.redis.get(f"rate_limit:user:{user_id}:concurrent") or 0
        ws_count = 0
        
        if workspace_id:
            ws_count = await self.redis.get(f"rate_limit:workspace:{workspace_id}:concurrent") or 0
        
        return {
            "user": int(user_count),
            "workspace": int(ws_count),
            "user_limit": settings.MAX_CONCURRENT_JOBS_PER_USER,
            "workspace_limit": settings.MAX_CONCURRENT_JOBS_PER_WORKSPACE
        }

rate_limiter = RateLimiter()

