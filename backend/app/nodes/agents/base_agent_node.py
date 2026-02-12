from ..base import BaseNode
from typing import Any, Dict, Optional

class AgentNode(BaseNode):
    """
    Wrapper for AI agents to fit the Node architecture.
    """
    node_type = "agent_wrapper"
    version = "1.0.0"
    category = "agents"

    def __init__(self, agent_instance, config: Optional[Dict[str, Any]] = None):
        super().__init__(config=config)
        self.agent = agent_instance

    async def execute(self, input_data: Any, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        try:
            # Handle both string and complex input
            task = str(input_data)
            if isinstance(input_data, dict):
                task = input_data.get("task") or input_data.get("input") or task

            # Execute agent (supporting both sync and potentially async run)
            if hasattr(self.agent, "arun"):
                result = await self.agent.arun(task, state=context)
            else:
                result = self.agent.run(task, state=context)
                
            return {
                "status": "success",
                "data": {"output": result}
            }
        except Exception as e:
            return {"status": "error", "error": f"Agent Node Failed: {str(e)}"}
