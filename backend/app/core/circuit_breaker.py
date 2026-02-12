from typing import Dict, Optional
from datetime import datetime, timedelta
import redis.asyncio as aioredis

class CircuitBreaker:
    """
    Circuit breaker pattern for node execution.
    Automatically disables failing nodes and re-enables them after recovery.
    """
    
    def __init__(self):
        self.redis: Optional[aioredis.Redis] = None
        # Configuration
        self.failure_threshold = 5  # Consecutive failures before opening circuit
        self.recovery_timeout = 300  # Seconds before attempting recovery (5 min)
        self.half_open_max_calls = 3  # Test calls in half-open state
    
    async def init_redis(self, redis_client: aioredis.Redis):
        """Initialize with the app's Redis instance."""
        self.redis = redis_client
        print("✅ Circuit Breaker initialized")
    
    async def record_success(self, node_type: str):
        """Record successful execution."""
        if not self.redis:
            return
        
        try:
            # Reset failure counter
            await self.redis.delete(f"circuit:failures:{node_type}")
            
            # Check if circuit was open/half-open
            state = await self.redis.get(f"circuit:state:{node_type}")
            if state in ["open", "half_open"]:
                # Close the circuit
                await self.redis.set(f"circuit:state:{node_type}", "closed")
                await self.redis.delete(f"circuit:opened_at:{node_type}")
                print(f"✅ Circuit CLOSED for {node_type} (recovered)")
                
        except Exception as e:
            print(f"⚠️ Circuit breaker error (success): {e}")
    
    async def record_failure(self, node_type: str, error: str):
        """Record failed execution and potentially open circuit."""
        if not self.redis:
            return
        
        try:
            # Increment failure counter
            failures = await self.redis.incr(f"circuit:failures:{node_type}")
            
            # Check if we should open the circuit
            if failures >= self.failure_threshold:
                current_state = await self.redis.get(f"circuit:state:{node_type}")
                
                if current_state != "open":
                    # Open the circuit
                    await self.redis.set(f"circuit:state:{node_type}", "open")
                    await self.redis.set(
                        f"circuit:opened_at:{node_type}",
                        datetime.utcnow().isoformat()
                    )
                    await self.redis.setex(
                        f"circuit:last_error:{node_type}",
                        3600,  # Keep error for 1 hour
                        error
                    )
                    print(f"🔴 Circuit OPENED for {node_type} after {failures} failures")
                    
        except Exception as e:
            print(f"⚠️ Circuit breaker error (failure): {e}")
    
    async def can_execute(self, node_type: str) -> tuple[bool, Optional[str]]:
        """
        Check if node execution is allowed.
        Returns (allowed, reason_if_not_allowed)
        """
        if not self.redis:
            return True, None
        
        try:
            state = await self.redis.get(f"circuit:state:{node_type}")
            
            if not state or state == "closed":
                return True, None
            
            if state == "open":
                # Check if recovery timeout has passed
                opened_at_str = await self.redis.get(f"circuit:opened_at:{node_type}")
                if opened_at_str:
                    opened_at = datetime.fromisoformat(opened_at_str)
                    if datetime.utcnow() - opened_at > timedelta(seconds=self.recovery_timeout):
                        # Move to half-open state
                        await self.redis.set(f"circuit:state:{node_type}", "half_open")
                        await self.redis.set(f"circuit:half_open_calls:{node_type}", "0")
                        print(f"🟡 Circuit HALF-OPEN for {node_type} (testing recovery)")
                        return True, None
                
                # Circuit is still open
                last_error = await self.redis.get(f"circuit:last_error:{node_type}")
                return False, f"Circuit breaker open due to repeated failures: {last_error or 'Unknown error'}"
            
            if state == "half_open":
                # Allow limited test calls
                calls = int(await self.redis.get(f"circuit:half_open_calls:{node_type}") or 0)
                if calls < self.half_open_max_calls:
                    await self.redis.incr(f"circuit:half_open_calls:{node_type}")
                    return True, None
                else:
                    return False, "Circuit breaker in half-open state (max test calls reached)"
            
            return True, None
            
        except Exception as e:
            print(f"⚠️ Circuit breaker check error: {e}")
            # Fail open - allow execution if circuit breaker has issues
            return True, None
    
    async def get_circuit_status(self, node_type: str) -> Dict:
        """Get current circuit status for a node type."""
        if not self.redis:
            return {"state": "unknown"}
        
        try:
            state = await self.redis.get(f"circuit:state:{node_type}") or "closed"
            failures = int(await self.redis.get(f"circuit:failures:{node_type}") or 0)
            last_error = await self.redis.get(f"circuit:last_error:{node_type}")
            
            status = {
                "node_type": node_type,
                "state": state,
                "consecutive_failures": failures,
                "threshold": self.failure_threshold,
                "last_error": last_error
            }
            
            if state == "open":
                opened_at_str = await self.redis.get(f"circuit:opened_at:{node_type}")
                if opened_at_str:
                    opened_at = datetime.fromisoformat(opened_at_str)
                    recovery_at = opened_at + timedelta(seconds=self.recovery_timeout)
                    status["opened_at"] = opened_at.isoformat()
                    status["recovery_at"] = recovery_at.isoformat()
                    status["seconds_until_recovery"] = max(0, int((recovery_at - datetime.utcnow()).total_seconds()))
            
            return status
            
        except Exception as e:
            print(f"⚠️ Error getting circuit status: {e}")
            return {"state": "error", "error": str(e)}
    
    async def get_all_circuits(self) -> list[Dict]:
        """Get status of all circuits."""
        if not self.redis:
            return []
        
        try:
            circuits = []
            async for key in self.redis.scan_iter(match="circuit:state:*"):
                node_type = key.replace("circuit:state:", "")
                status = await self.get_circuit_status(node_type)
                circuits.append(status)
            
            return circuits
            
        except Exception as e:
            print(f"⚠️ Error getting all circuits: {e}")
            return []
    
    async def reset_circuit(self, node_type: str):
        """Manually reset a circuit (admin override)."""
        if not self.redis:
            return
        
        try:
            await self.redis.delete(f"circuit:state:{node_type}")
            await self.redis.delete(f"circuit:failures:{node_type}")
            await self.redis.delete(f"circuit:opened_at:{node_type}")
            await self.redis.delete(f"circuit:last_error:{node_type}")
            await self.redis.delete(f"circuit:half_open_calls:{node_type}")
            print(f"🔄 Circuit RESET for {node_type} (manual override)")
            
        except Exception as e:
            print(f"⚠️ Error resetting circuit: {e}")

circuit_breaker = CircuitBreaker()
