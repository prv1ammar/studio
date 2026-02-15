import os
import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict

class DeadLetterQueue:
    """
    Stores failed execution payloads for manual inspection and replay.
    """
    def __init__(self, dlq_dir: str = "backend/data/dlq"):
        self.dlq_path = Path(dlq_dir)
        self.dlq_path.mkdir(parents=True, exist_ok=True)

    def capture(self, execution_id: str, graph: Dict[str, Any], error: str, context: Dict[str, Any]):
        payload = {
            "execution_id": execution_id,
            "timestamp": datetime.now().isoformat(),
            "error": error,
            "graph": graph,
            "context_summary": {k: str(v)[:100] for k, v in context.items() if k != "engine"}
        }
        file_path = self.dlq_path / f"failed_{execution_id}.json"
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=4)
        print(f" Sent execution {execution_id} to DLQ.")

dlq = DeadLetterQueue()

