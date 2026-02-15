import asyncio
from typing import Dict, Any, Optional
from functools import wraps
from app.core.config import settings

class TimeoutError(Exception):
    """Raised when a node execution exceeds the allowed timeout."""
    pass

def with_timeout(timeout_seconds: Optional[int] = None):
    """
    Decorator to enforce strict timeout on async node execution.
    Prevents zombie nodes from hanging workers indefinitely.
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            timeout = timeout_seconds or settings.NODE_EXECUTION_TIMEOUT
            try:
                return await asyncio.wait_for(func(*args, **kwargs), timeout=timeout)
            except asyncio.TimeoutError:
                raise TimeoutError(f"Node execution exceeded {timeout}s timeout")
        return wrapper
    return decorator

async def execute_with_timeout(coro, timeout: int = None):
    """
    Utility function to execute any coroutine with a timeout guard.
    Usage: result = await execute_with_timeout(node.run(input), timeout=30)
    """
    timeout = timeout or settings.NODE_EXECUTION_TIMEOUT
    try:
        return await asyncio.wait_for(coro, timeout=timeout)
    except asyncio.TimeoutError:
        raise TimeoutError(f"Execution exceeded {timeout}s timeout")

