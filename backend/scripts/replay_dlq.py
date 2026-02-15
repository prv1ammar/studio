import sys
import os
import json
import asyncio
from pathlib import Path

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from backend.app.core.engine import engine

async def replay_execution(execution_id: str):
    dlq_dir = Path("backend/data/dlq")
    file_path = dlq_dir / f"failed_{execution_id}.json"
    
    if not file_path.exists():
        print(f"Error: DLQ file for execution {execution_id} not found.")
        return

    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    graph = data["graph"]
    message = data["context_summary"].get("initial_query", "Replay Execution") 
    # context_summary might have truncated info, so be careful. 
    # Ideally, we should have stored full context in DLQ for full replay.
    # But for now, let's try to run the graph.

    print(f"Replaying execution {execution_id}...")
    try:
        result = await engine.process_workflow(
            graph_data=graph,
            message=message,
            execution_id=f"replay_{execution_id}",
            context={"mode": "replay"}
        )
        print("Replay Success:", result)
    except Exception as e:
        print("Replay Failed:", e)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python replay_dlq.py <execution_id>")
        sys.exit(1)
    
    asyncio.run(replay_execution(sys.argv[1]))
