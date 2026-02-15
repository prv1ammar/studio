import asyncio
from typing import Any, Dict, List, Optional
from app.nodes.base import BaseNode
from app.nodes.factory import register_node
from pydantic import BaseModel, Field
from sqlmodel import select
from app.db.session import async_session
from app.db.models import Workflow
import json

class ParallelMapConfig(BaseModel):
    sub_workflow_id: str = Field(..., description="The ID of the workflow to run for each item")
    concurrency_limit: int = Field(default=5, ge=1, le=20, description="Max number of parallel executions")

class ParallelMapInput(BaseModel):
    items: List[Any] = Field(..., description="The list of data items to process in parallel")

@register_node("parallel_map")
class ParallelMapNode(BaseNode):
    """
    High-Performance Orchestration: Parallel Map.
    Processes an array of items concurrently using a sub-workflow.
    Equivalent to a 'Map/Reduce' pattern in data engineering.
    """
    name = "Parallel Map"
    description = "Process a list of items concurrently across multiple workers."
    category = "Orchestration"
    node_type = "parallel_map"
    
    config_model = ParallelMapConfig
    input_model = ParallelMapInput

    async def execute(self, input_data: ParallelMapInput, context: Optional[Dict[str, Any]] = None) -> List[Any]:
        sub_wf_id = self.get_config("sub_workflow_id")
        concurrency = self.get_config("concurrency_limit")
        items = input_data.items
        
        # 1. Fetch Workflow
        async with async_session() as db:
            res = await db.execute(select(Workflow).where(Workflow.id == sub_wf_id))
            workflow = res.scalar_one_or_none()
            if not workflow:
                raise ValueError(f"Target sub-workflow '{sub_wf_id}' not found.")
            
            wf_definition = workflow.definition

        # 2. Parallel Execution with Semaphore to respect concurrency limit
        semaphore = asyncio.Semaphore(concurrency)
        from app.core.engine import engine

        async def run_item(item):
            async with semaphore:
                print(f"[PARALLEL-MAP] Processing item: {str(item)[:50]}...")
                result_text = await engine.process_workflow(
                    wf_definition,
                    message=json.dumps(item) if not isinstance(item, str) else item,
                    context={
                        "is_parallel_mapped": True,
                        "parent_execution_id": context.get("execution_id") if context else None
                    }
                )
                try:
                    return json.loads(result_text)
                except:
                    return result_text

        # Start all tasks
        tasks = [run_item(item) for item in items]
        results = await asyncio.gather(*tasks)
        
        return results
