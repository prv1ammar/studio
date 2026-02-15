import redis.asyncio as aioredis
import hashlib
import json
from typing import Any, Optional, Dict
from app.core.config import settings
import time

class CacheManager:
    """
    Intelligent Redis-backed cache for node execution results.
    Reduces redundant API calls and speeds up workflow execution.
    """
    
    def __init__(self):
        self.redis: Optional[aioredis.Redis] = None
        self.stats = {
            "hits": 0,
            "misses": 0,
            "writes": 0
        }
    
    async def init_redis(self, redis_client: aioredis.Redis):
        """Initialize with the app's Redis instance."""
        self.redis = redis_client
        print(f" Cache Manager initialized (TTL: {settings.CACHE_TTL}s)")
    
    def _generate_cache_key(self, node_type: str, input_data: Any, config: Dict[str, Any]) -> str:
        """
        Generate deterministic cache key based on node type, input, and config.
        Uses SHA256 hash for consistent key generation.
        """
        # Create a deterministic string representation
        cache_input = {
            "node_type": node_type,
            "input": str(input_data),
            "config": {k: v for k, v in (config or {}).items() if k not in ["retry_count", "timeout", "cacheable"]}
        }
        
        # Generate hash
        cache_str = json.dumps(cache_input, sort_keys=True)
        hash_key = hashlib.sha256(cache_str.encode()).hexdigest()[:16]
        
        return f"cache:node:{node_type}:{hash_key}"
    
    async def get(self, node_type: str, input_data: Any, config: Dict[str, Any]) -> Optional[Any]:
        """
        Retrieve cached result if available.
        Returns None if cache miss or caching disabled.
        """
        if not self.redis or not settings.ENABLE_RESULT_CACHING:
            return None
        
        # Check if this node type is cacheable
        if not config or not config.get("cacheable", False):
            return None
        
        try:
            cache_key = self._generate_cache_key(node_type, input_data, config)
            cached_data = await self.redis.get(cache_key)
            
            if cached_data:
                self.stats["hits"] += 1
                result = json.loads(cached_data)
                print(f" Cache HIT: {node_type} (key: {cache_key[:20]}...)")
                return result
            
            self.stats["misses"] += 1
            return None
            
        except Exception as e:
            print(f" Cache get error: {e}")
            return None
    
    async def set(self, node_type: str, input_data: Any, config: Dict[str, Any], result: Any):
        """
        Store result in cache with TTL.
        Only caches if node is marked as cacheable and result is serializable.
        """
        if not self.redis or not settings.ENABLE_RESULT_CACHING:
            return
        
        # Check if this node type is cacheable
        if not config or not config.get("cacheable", False):
            return
        
        # Don't cache errors
        if isinstance(result, dict) and "error" in result:
            return
        
        try:
            cache_key = self._generate_cache_key(node_type, input_data, config)
            
            # Get custom TTL or use default
            ttl = config.get("cache_ttl", settings.CACHE_TTL)
            
            # Serialize and store
            cached_data = json.dumps(result)
            await self.redis.setex(cache_key, ttl, cached_data)
            
            self.stats["writes"] += 1
            print(f" Cache SET: {node_type} (TTL: {ttl}s, key: {cache_key[:20]}...)")
            
        except (TypeError, ValueError) as e:
            # Result not serializable, skip caching
            print(f" Cache skip (not serializable): {node_type}")
        except Exception as e:
            print(f" Cache set error: {e}")
    
    async def invalidate(self, pattern: str = None):
        """
        Invalidate cache entries matching pattern.
        If no pattern provided, clears all node caches.
        """
        if not self.redis:
            return
        
        try:
            pattern = pattern or "cache:node:*"
            keys = []
            
            async for key in self.redis.scan_iter(match=pattern):
                keys.append(key)
            
            if keys:
                await self.redis.delete(*keys)
                print(f" Invalidated {len(keys)} cache entries (pattern: {pattern})")
                return len(keys)
            
            return 0
            
        except Exception as e:
            print(f" Cache invalidation error: {e}")
            return 0
    
    async def invalidate_node_type(self, node_type: str):
        """Invalidate all cache entries for a specific node type."""
        return await self.invalidate(f"cache:node:{node_type}:*")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        total_requests = self.stats["hits"] + self.stats["misses"]
        hit_rate = (self.stats["hits"] / total_requests * 100) if total_requests > 0 else 0
        
        return {
            "hits": self.stats["hits"],
            "misses": self.stats["misses"],
            "writes": self.stats["writes"],
            "total_requests": total_requests,
            "hit_rate": round(hit_rate, 2),
            "enabled": settings.ENABLE_RESULT_CACHING
        }
    
    def reset_stats(self):
        """Reset statistics counters."""
        self.stats = {"hits": 0, "misses": 0, "writes": 0}

cache_manager = CacheManager()

