import redis.asyncio as aioredis
import time
import asyncio
from typing import Dict, List, Optional, Any
from datetime import datetime
import socket

class WorkerMonitor:
    """
    Real-time worker health monitoring and queue metrics.
    Tracks worker heartbeats, queue depths, and system health.
    """
    
    def __init__(self):
        self.redis: Optional[aioredis.Redis] = None
        self.worker_id: str = f"{socket.gethostname()}-{id(self)}"
        self.heartbeat_interval = 10  # seconds
        self.heartbeat_task: Optional[asyncio.Task] = None
    
    async def init_redis(self, redis_client: aioredis.Redis):
        """Initialize with the app's Redis instance."""
        self.redis = redis_client
        print(f"✅ Worker Monitor initialized (ID: {self.worker_id})")
    
    async def start_heartbeat(self, worker_type: str = "default"):
        """
        Start sending periodic heartbeats to Redis.
        Called by workers on startup.
        """
        if not self.redis:
            return
        
        async def heartbeat_loop():
            while True:
                try:
                    await self.send_heartbeat(worker_type)
                    await asyncio.sleep(self.heartbeat_interval)
                except asyncio.CancelledError:
                    break
                except Exception as e:
                    print(f"⚠️ Heartbeat error: {e}")
                    await asyncio.sleep(self.heartbeat_interval)
        
        self.heartbeat_task = asyncio.create_task(heartbeat_loop())
        print(f"💓 Heartbeat started for worker {self.worker_id}")
    
    async def send_heartbeat(self, worker_type: str = "default"):
        """Send a single heartbeat to Redis."""
        if not self.redis:
            return
        
        heartbeat_data = {
            "worker_id": self.worker_id,
            "worker_type": worker_type,
            "timestamp": time.time(),
            "hostname": socket.gethostname()
        }
        
        key = f"worker:heartbeat:{self.worker_id}"
        await self.redis.setex(
            key,
            self.heartbeat_interval * 3,  # TTL = 3x heartbeat interval
            str(heartbeat_data)
        )
    
    async def stop_heartbeat(self):
        """Stop sending heartbeats."""
        if self.heartbeat_task:
            self.heartbeat_task.cancel()
            try:
                await self.heartbeat_task
            except asyncio.CancelledError:
                pass
        
        # Remove heartbeat key
        if self.redis:
            await self.redis.delete(f"worker:heartbeat:{self.worker_id}")
        
        print(f"💔 Heartbeat stopped for worker {self.worker_id}")
    
    async def get_active_workers(self) -> List[Dict[str, Any]]:
        """Get list of all active workers based on heartbeats."""
        if not self.redis:
            return []
        
        workers = []
        async for key in self.redis.scan_iter(match="worker:heartbeat:*"):
            try:
                data = await self.redis.get(key)
                if data:
                    worker_info = eval(data)  # Safe since we control the data
                    worker_info["last_seen"] = datetime.fromtimestamp(
                        worker_info["timestamp"]
                    ).isoformat()
                    workers.append(worker_info)
            except Exception as e:
                print(f"⚠️ Error reading worker data: {e}")
        
        return workers
    
    async def get_queue_depth(self, queue_name: str = "arq:queue") -> int:
        """Get the number of pending jobs in a queue."""
        if not self.redis:
            return 0
        
        try:
            depth = await self.redis.llen(queue_name)
            return depth or 0
        except Exception as e:
            print(f"⚠️ Error getting queue depth: {e}")
            return 0
    
    async def get_queue_stats(self) -> Dict[str, Any]:
        """Get comprehensive queue statistics."""
        if not self.redis:
            return {}
        
        stats = {
            "default_queue": await self.get_queue_depth("arq:queue"),
            "webhook_queue": await self.get_queue_depth("arq:queue:webhook"),
            "total_pending": 0
        }
        
        stats["total_pending"] = stats["default_queue"] + stats["webhook_queue"]
        return stats
    
    async def get_health_status(self) -> Dict[str, Any]:
        """Get overall system health status."""
        workers = await self.get_active_workers()
        queue_stats = await self.get_queue_stats()
        
        # Determine health status
        worker_count = len(workers)
        total_pending = queue_stats.get("total_pending", 0)
        
        if worker_count == 0:
            status = "critical"
            message = "No active workers"
        elif total_pending > 100:
            status = "warning"
            message = f"High queue depth ({total_pending} jobs)"
        else:
            status = "healthy"
            message = "All systems operational"
        
        return {
            "status": status,
            "message": message,
            "workers": {
                "active": worker_count,
                "details": workers
            },
            "queues": queue_stats,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    async def cleanup_dead_workers(self):
        """Remove heartbeat keys for workers that haven't checked in."""
        # Redis TTL handles this automatically, but we can add manual cleanup if needed
        pass

worker_monitor = WorkerMonitor()
