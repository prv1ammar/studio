import asyncio
from arq import create_pool
from arq.connections import RedisSettings
from app.core.engine import engine
from app.core.config import settings
import json
from typing import Dict, Any

async def run_workflow_task(ctx, graph_data: Dict[str, Any], message: str, job_id: str, start_node_id: str = None, initial_outputs: Dict[str, Any] = None):
    """
    Background task to process a workflow.
    Uses Redis to broadcast updates back to the API/UI.
    """
    print(f"🚀 [Worker] Starting job {job_id} {'(Resume from '+start_node_id+')' if start_node_id else ''}")
    
    # Create a broadcaster that sends events to Redis Pub/Sub
    redis = ctx['redis']
    
    async def redis_broadcaster(event_type: str, node_id: str, data: Any = None):
        payload = {
            "type": event_type,
            "nodeId": node_id,
            "data": data,
            "jobId": job_id
        }
        await redis.publish(f"workflow_updates_{job_id}", json.dumps(payload))
    
    try:
        # Execute workflow
        result = await engine.process_workflow(
            graph_data, 
            message, 
            broadcaster=redis_broadcaster, 
            execution_id=job_id,
            start_node_id=start_node_id,
            initial_outputs=initial_outputs
        )
        
        # Broadcast final result
        await redis.publish(f"workflow_updates_{job_id}", json.dumps({
            "type": "workflow_completed",
            "jobId": job_id,
            "result": result
        }))
        print(f"✅ [Worker] Job {job_id} completed successfully.")
    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        print(f"❌ [Worker] Job {job_id} failed: {str(e)}")
        await redis.publish(f"workflow_updates_{job_id}", json.dumps({
            "type": "workflow_failed",
            "jobId": job_id,
            "error": str(e),
            "trace": error_trace
        }))

async def startup(ctx):
    print("👷 Worker starting up...")

async def shutdown(ctx):
    print("👷 Worker shutting down...")

class WorkerSettings:
    """
    ARQ Worker configuration
    """
    functions = [run_workflow_task]
    redis_settings = RedisSettings.from_dsn(settings.REDIS_URL)
    on_startup = startup
    on_shutdown = shutdown
    job_timeout = settings.WORKFLOW_TIMEOUT
