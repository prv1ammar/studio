import asyncio
from app.db.session import async_session
from app.db.models import Execution, NodeExecution
from sqlmodel import select
import json

async def show_recent_logs():
    async with async_session() as session:
        # Get last execution
        result = await session.execute(select(Execution).order_by(Execution.created_at.desc()).limit(1))
        execution = result.scalar_one_or_none()
        
        if not execution:
            print("No executions found.")
            return

        print(f"\n[Execution ID: {execution.id}]")
        print(f"Status: {execution.status}")
        
        # Get node executions for this run
        node_result = await session.execute(
            select(NodeExecution).where(NodeExecution.execution_id == execution.id)
        )
        node_execs = node_result.scalars().all()
        
        print("\nNode Execution History:")
        for ne in node_execs:
            print(f"  - Node: {ne.node_id} ({ne.node_type})")
            print(f"    Status: {ne.status}")
            print(f"    Execution Time: {ne.execution_time:.3f}s")
            print(f"    Logs: {json.dumps(ne.logs, indent=4) if ne.logs else '[]'}")
            if ne.error:
                print(f"    Error: {ne.error}")
            print("-" * 20)

if __name__ == "__main__":
    asyncio.run(show_recent_logs())
