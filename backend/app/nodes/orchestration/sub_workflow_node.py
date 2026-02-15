from typing import Any, Dict, Optional
from app.nodes.base import BaseNode
from app.nodes.factory import register_node
from pydantic import BaseModel, Field
from sqlmodel import select
from app.db.session import async_session
from app.db.models import Workflow
import json

class SubWorkflowConfig(BaseModel):
    workflow_id: str = Field(..., description="The ID of the sub-workflow to execute")
    wait_for_completion: bool = Field(default=True, description="Whether to wait for the sub-workflow to finish and return its result")

class SubWorkflowInput(BaseModel):
    input_data: Optional[Dict[str, Any]] = None

@register_node("sub_workflow")
class SubWorkflowNode(BaseNode):
    """
    Modular Orchestration: Sub-Workflow.
    Allows reusability by calling another workflow as a node.
    """
    name = "Execute Sub-Workflow"
    description = "Run another workflow as a modular component."
    category = "Orchestration"
    node_type = "sub_workflow"
    
    config_model = SubWorkflowConfig
    input_model = SubWorkflowInput

    async def execute(self, input_data: SubWorkflowInput, context: Optional[Dict[str, Any]] = None) -> Any:
        # 1. Fetch Workflow from DB
        workflow_id = self.get_config("workflow_id")
        
        async with async_session() as db:
            result = await db.execute(select(Workflow).where(Workflow.id == workflow_id))
            workflow = result.scalar_one_or_none()
            
            if not workflow:
                raise ValueError(f"Sub-workflow '{workflow_id}' not found.")
            
            # 2. Preparation
            graph_definition = workflow.definition
            sub_message = json.dumps(input_data.input_data) if input_data.input_data else context.get("message", "")
            
            # 3. Execution
            from app.core.engine import engine
            
            # In a real system, we'd handle recursion depth here to prevent infinite loops
            
            if self.get_config("wait_for_completion"):
                # Run synchronously (blocking this node until finish)
                print(f"[SUB-WORKFLOW] Executing '{workflow.name}' synchronously...")
                result_text = await engine.process_workflow(
                    graph_definition,
                    message=sub_message,
                    context={
                        "parent_execution_id": context.get("execution_id") if context else None,
                        "is_sub_workflow": True,
                        "initial_data": input_data.input_data
                    }
                )
                
                try:
                    return json.loads(result_text)
                except:
                    return {"result": result_text}
            else:
                # Fire and forget
                import asyncio
                asyncio.create_task(
                    engine.process_workflow(
                        graph_definition,
                        message=sub_message,
                        context={"is_sub_workflow": True}
                    )
                )
                return {"status": "triggered", "workflow": workflow.name}
