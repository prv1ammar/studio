import os
import sys
# Add backend to path
sys.path.append(os.path.abspath("backend"))

import asyncio
from arq import create_pool
from arq.connections import RedisSettings
from app.core.config import settings

async def main():
    redis = await create_pool(RedisSettings.from_dsn(settings.REDIS_URL))
    job_id = "test-job-manual"
    graph_data = {
        "nodes": [{"id": "node-1", "type": "chatInput", "data": {"id": "chatInput", "label": "Input"}}],
        "edges": []
    }
    print(f"Queueing job {job_id}...")
    await redis.enqueue_job(
        'run_workflow_task',
        graph_data=graph_data,
        message="Hello from test script",
        job_id=job_id,
        user_id="test-user-id"
    )
    print("Job queued. Check worker logs.")

if __name__ == "__main__":
    asyncio.run(main())
