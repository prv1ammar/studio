import redis.asyncio as aioredis
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from collections import defaultdict
import json

class AnalyticsTracker:
    """
    Usage analytics and insights system.
    Tracks execution patterns, node usage, errors, and performance metrics.
    """
    
    def __init__(self):
        self.redis: Optional[aioredis.Redis] = None
    
    async def init_redis(self, redis_client: aioredis.Redis):
        """Initialize with the app's Redis instance."""
        self.redis = redis_client
        print(" Analytics Tracker initialized")
    
    async def track_workflow_execution(
        self, 
        user_id: str, 
        workspace_id: Optional[str],
        workflow_id: str,
        execution_id: str,
        status: str,  # "started", "completed", "failed"
        duration: Optional[float] = None,
        error: Optional[str] = None
    ):
        """Track workflow execution event."""
        if not self.redis:
            return
        
        try:
            event = {
                "user_id": user_id,
                "workspace_id": workspace_id,
                "workflow_id": workflow_id,
                "execution_id": execution_id,
                "status": status,
                "duration": duration,
                "error": error,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            # Store in time-series list (last 1000 events)
            await self.redis.lpush("analytics:workflow_executions", json.dumps(event))
            await self.redis.ltrim("analytics:workflow_executions", 0, 999)
            
            # Increment counters
            today = datetime.utcnow().strftime("%Y-%m-%d")
            await self.redis.hincrby(f"analytics:daily:{today}", f"workflow_{status}", 1)
            
            if status == "completed" and duration:
                # Track execution time
                await self.redis.lpush(f"analytics:durations:{workflow_id}", duration)
                await self.redis.ltrim(f"analytics:durations:{workflow_id}", 0, 99)
            
        except Exception as e:
            print(f" Analytics tracking error: {e}")
    
    async def track_node_execution(
        self,
        node_type: str,
        user_id: str,
        workspace_id: Optional[str],
        execution_id: str,
        duration: float,
        success: bool,
        cached: bool = False
    ):
        """Track individual node execution."""
        if not self.redis:
            return
        
        try:
            # Increment node usage counter
            await self.redis.hincrby("analytics:node_usage", node_type, 1)
            
            # Track success/failure
            status_key = "success" if success else "failure"
            await self.redis.hincrby(f"analytics:node_status:{node_type}", status_key, 1)
            
            # Track cache hits
            if cached:
                await self.redis.hincrby("analytics:cache_hits", node_type, 1)
            
            # Track execution time
            await self.redis.lpush(f"analytics:node_durations:{node_type}", duration)
            await self.redis.ltrim(f"analytics:node_durations:{node_type}", 0, 99)
            
        except Exception as e:
            print(f" Node analytics error: {e}")
    
    async def track_api_call(
        self,
        api_type: str,  # "openai", "google", etc.
        user_id: str,
        workspace_id: Optional[str],
        tokens: Optional[int] = None,
        cost: Optional[float] = None
    ):
        """Track external API calls and costs."""
        if not self.redis:
            return
        
        try:
            today = datetime.utcnow().strftime("%Y-%m-%d")
            
            # Increment API call counter
            await self.redis.hincrby(f"analytics:api_calls:{today}", api_type, 1)
            
            # Track tokens (for LLMs)
            if tokens:
                await self.redis.hincrby(f"analytics:tokens:{today}", api_type, tokens)
            
            # Track costs
            if cost:
                current = await self.redis.hget(f"analytics:costs:{today}", api_type) or "0"
                new_cost = float(current) + cost
                await self.redis.hset(f"analytics:costs:{today}", api_type, str(new_cost))
            
        except Exception as e:
            print(f" API tracking error: {e}")
    
    async def get_node_usage_stats(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Get most-used nodes."""
        if not self.redis:
            return []
        
        try:
            usage = await self.redis.hgetall("analytics:node_usage")
            
            # Convert to list and sort
            stats = [
                {"node_type": k, "count": int(v)}
                for k, v in usage.items()
            ]
            stats.sort(key=lambda x: x["count"], reverse=True)
            
            return stats[:limit]
            
        except Exception as e:
            print(f" Error getting node stats: {e}")
            return []
    
    async def get_workflow_stats(self, days: int = 7) -> Dict[str, Any]:
        """Get workflow execution statistics for the last N days."""
        if not self.redis:
            return {}
        
        try:
            stats = {
                "total_executions": 0,
                "completed": 0,
                "failed": 0,
                "success_rate": 0,
                "daily_breakdown": []
            }
            
            for i in range(days):
                date = (datetime.utcnow() - timedelta(days=i)).strftime("%Y-%m-%d")
                daily_data = await self.redis.hgetall(f"analytics:daily:{date}")
                
                completed = int(daily_data.get("workflow_completed", 0))
                failed = int(daily_data.get("workflow_failed", 0))
                total = completed + failed
                
                stats["total_executions"] += total
                stats["completed"] += completed
                stats["failed"] += failed
                
                stats["daily_breakdown"].append({
                    "date": date,
                    "total": total,
                    "completed": completed,
                    "failed": failed
                })
            
            # Calculate success rate
            if stats["total_executions"] > 0:
                stats["success_rate"] = round(
                    (stats["completed"] / stats["total_executions"]) * 100, 2
                )
            
            return stats
            
        except Exception as e:
            print(f" Error getting workflow stats: {e}")
            return {}
    
    async def get_performance_insights(self) -> Dict[str, Any]:
        """Get performance insights and bottlenecks."""
        if not self.redis:
            return {}
        
        try:
            insights = {
                "slowest_nodes": [],
                "most_failed_nodes": [],
                "cache_efficiency": {}
            }
            
            # Get all node types
            node_usage = await self.redis.hgetall("analytics:node_usage")
            
            # Analyze each node
            node_performance = []
            for node_type in node_usage.keys():
                # Get average duration
                durations = await self.redis.lrange(f"analytics:node_durations:{node_type}", 0, -1)
                if durations:
                    avg_duration = sum(float(d) for d in durations) / len(durations)
                else:
                    avg_duration = 0
                
                # Get success/failure counts
                status = await self.redis.hgetall(f"analytics:node_status:{node_type}")
                success = int(status.get("success", 0))
                failure = int(status.get("failure", 0))
                total = success + failure
                failure_rate = (failure / total * 100) if total > 0 else 0
                
                # Get cache hits
                cache_hits = int(await self.redis.hget("analytics:cache_hits", node_type) or 0)
                cache_rate = (cache_hits / total * 100) if total > 0 else 0
                
                node_performance.append({
                    "node_type": node_type,
                    "avg_duration": round(avg_duration, 2),
                    "failure_rate": round(failure_rate, 2),
                    "cache_rate": round(cache_rate, 2),
                    "total_executions": total
                })
            
            # Sort by duration (slowest first)
            node_performance.sort(key=lambda x: x["avg_duration"], reverse=True)
            insights["slowest_nodes"] = node_performance[:10]
            
            # Sort by failure rate
            node_performance.sort(key=lambda x: x["failure_rate"], reverse=True)
            insights["most_failed_nodes"] = [n for n in node_performance[:10] if n["failure_rate"] > 0]
            
            return insights
            
        except Exception as e:
            print(f" Error getting insights: {e}")
            return {}
    
    async def get_cost_analysis(self, days: int = 30) -> Dict[str, Any]:
        """Get API cost analysis."""
        if not self.redis:
            return {}
        
        try:
            analysis = {
                "total_cost": 0,
                "total_tokens": 0,
                "by_api": {},
                "daily_breakdown": []
            }
            
            for i in range(days):
                date = (datetime.utcnow() - timedelta(days=i)).strftime("%Y-%m-%d")
                
                # Get costs for this day
                costs = await self.redis.hgetall(f"analytics:costs:{date}")
                tokens = await self.redis.hgetall(f"analytics:tokens:{date}")
                
                daily_cost = sum(float(v) for v in costs.values())
                daily_tokens = sum(int(v) for v in tokens.values())
                
                analysis["total_cost"] += daily_cost
                analysis["total_tokens"] += daily_tokens
                
                analysis["daily_breakdown"].append({
                    "date": date,
                    "cost": round(daily_cost, 2),
                    "tokens": daily_tokens
                })
                
                # Aggregate by API type
                for api_type, cost in costs.items():
                    if api_type not in analysis["by_api"]:
                        analysis["by_api"][api_type] = {"cost": 0, "tokens": 0}
                    analysis["by_api"][api_type]["cost"] += float(cost)
                
                for api_type, token_count in tokens.items():
                    if api_type not in analysis["by_api"]:
                        analysis["by_api"][api_type] = {"cost": 0, "tokens": 0}
                    analysis["by_api"][api_type]["tokens"] += int(token_count)
            
            # Round totals
            analysis["total_cost"] = round(analysis["total_cost"], 2)
            
            return analysis
            
        except Exception as e:
            print(f" Error getting cost analysis: {e}")
            return {}

analytics_tracker = AnalyticsTracker()

