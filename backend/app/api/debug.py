from fastapi import APIRouter, Depends, HTTPException
from typing import Dict, Any, Optional
from app.core.config import settings
import redis.asyncio as aioredis

router = APIRouter()

async def get_redis():
    return aioredis.from_url(settings.REDIS_URL, decode_responses=True)

@router.post("/{execution_id}/breakpoint/{node_id}")
async def set_breakpoint(execution_id: str, node_id: str, action: str = "set", r: aioredis.Redis = Depends(get_redis)):
    """
    Sets or removes a breakpoint for a specific node in a running/startable execution.
    """
    key = f"breakpoint_{execution_id}_{node_id}"
    if action == "set":
        await r.set(key, "1")
        return {"status": "breakpoint_set", "node_id": node_id}
    else:
        await r.delete(key)
        return {"status": "breakpoint_removed", "node_id": node_id}

@router.post("/{execution_id}/resume")
async def resume_execution(execution_id: str, node_id: Optional[str] = None, r: aioredis.Redis = Depends(get_redis)):
    """
    Resumes a paused execution by removing the breakpoint flag.
    """
    if node_id:
        await r.delete(f"breakpoint_{execution_id}_{node_id}")
    else:
        # Clear all breakpoints for this execution
        keys = await r.keys(f"breakpoint_{execution_id}_*")
        if keys:
            await r.delete(*keys)
            
    return {"status": "resumed"}

@router.post("/{execution_id}/step")
async def step_over(execution_id: str, r: aioredis.Redis = Depends(get_redis)):
    """
    Signals the engine to execute the CURRENT node and pause at the NEXT one.
    """
    await r.set(f"step_{execution_id}", "1")
    return {"status": "step_signal_sent"}
