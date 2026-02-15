import asyncio
import os
from dotenv import load_dotenv
load_dotenv()
from arq import create_pool
from arq.connections import RedisSettings
from app.core.engine import engine
from app.core.config import settings
from app.core.timeout import execute_with_timeout, TimeoutError
from app.core.rate_limiter import rate_limiter
import json
from typing import Dict, Any

async def run_workflow_task(ctx, graph_data: Dict[str, Any], message: str, job_id: str, start_node_id: str = None, initial_outputs: Dict[str, Any] = None, user_id: str = None, workspace_id: str = None, queue: str = "default"):
    """
    Background task to process a workflow with timeout and rate limiting.
    Uses Redis to broadcast updates back to the API/UI.
    """
    print(f"[START] [Worker:{queue}] Starting job {job_id} {'(Resume from '+start_node_id+')' if start_node_id else ''}")
    
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
        # Execute workflow with global timeout
        result = await execute_with_timeout(
            engine.process_workflow(
                graph_data, 
                message, 
                broadcaster=redis_broadcaster, 
                execution_id=job_id,
                start_node_id=start_node_id,
                initial_outputs=initial_outputs,
                context={"user_id": user_id, "workspace_id": workspace_id}
            ),
            timeout=settings.WORKFLOW_TIMEOUT
        )
        
        # Broadcast final result
        await redis.publish(f"workflow_updates_{job_id}", json.dumps({
            "type": "workflow_completed",
            "jobId": job_id,
            "result": result
        }))
        print(f"[OK] [Worker:{queue}] Job {job_id} completed successfully.")
        
    except TimeoutError as e:
        error_msg = f"Workflow exceeded {settings.WORKFLOW_TIMEOUT}s global timeout"
        print(f"[TIMEOUT] [Worker:{queue}] Job {job_id}: {error_msg}")
        await redis.publish(f"workflow_updates_{job_id}", json.dumps({
            "type": "workflow_failed",
            "jobId": job_id,
            "error": error_msg,
            "error_type": "timeout"
        }))
        
    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        print(f"[ERROR] [Worker:{queue}] Job {job_id} failed: {str(e)}")
        await redis.publish(f"workflow_updates_{job_id}", json.dumps({
            "type": "workflow_failed",
            "jobId": job_id,
            "error": str(e),
            "trace": error_trace
        }))
    
    finally:
        # Release rate limit slots
        if user_id:
            await rate_limiter.release(user_id, workspace_id)

async def run_webhook_task(ctx, webhook_data: Dict[str, Any], job_id: str):
    """
    Dedicated webhook processor for external triggers.
    Isolated from main workflow queue for guaranteed availability.
    """
    print(f"[WEBHOOK] Processing webhook {job_id}")
    redis = ctx['redis']
    
    try:
        # Process webhook logic here
        # This is a placeholder for webhook-specific processing
        result = {"status": "processed", "webhook_id": job_id}
        
        await redis.publish(f"webhook_updates_{job_id}", json.dumps({
            "type": "webhook_processed",
            "jobId": job_id,
            "result": result
        }))
        
    except Exception as e:
        print(f"[WEBHOOK ERROR] {job_id}: {str(e)}")
        await redis.publish(f"webhook_updates_{job_id}", json.dumps({
            "type": "webhook_failed",
            "jobId": job_id,
            "error": str(e)
        }))

async def startup(ctx):
    print("[INFO] Worker starting up...")
    # Initialize rate limiter with Redis
    await rate_limiter.init_redis(ctx['redis'])
    print(f"[INFO] Rate limiter initialized (User: {settings.MAX_CONCURRENT_JOBS_PER_USER}, Workspace: {settings.MAX_CONCURRENT_JOBS_PER_WORKSPACE})")
    
    # Initialize and start worker monitor
    from app.core.worker_monitor import worker_monitor
    await worker_monitor.init_redis(ctx['redis'])
    await worker_monitor.start_heartbeat(worker_type="default")

async def shutdown(ctx):
    print("[INFO] Worker shutting down...")
    # Stop worker monitor
    from app.core.worker_monitor import worker_monitor
    await worker_monitor.stop_heartbeat()

class WorkerSettings:
    """
    ARQ Worker configuration with multi-queue support
    """
    functions = [run_workflow_task, run_webhook_task]
    redis_settings = RedisSettings.from_dsn(settings.REDIS_URL)
    on_startup = startup
    on_shutdown = shutdown
    job_timeout = settings.WORKFLOW_TIMEOUT
    max_jobs = settings.WORKER_CONCURRENCY  # Concurrent jobs per worker
    queue_name = os.getenv("WORKER_QUEUE", "default")  # Configurable for multi-region support

