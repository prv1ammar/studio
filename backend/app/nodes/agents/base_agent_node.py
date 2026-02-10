from ..base import BaseNode
from typing import Any, Dict, Optional

class AgentNode(BaseNode):
    """
    Wrapper for AI agents to fit the Node architecture.
    """
    def __init__(self, agent_instance, config: Optional[Dict[str, Any]] = None):
        super().__init__(config=config)
        self.agent = agent_instance

    async def execute(self, input_data: str, context: Optional[Dict[str, Any]] = None) -> str:
        # Most existing agents have a sync run method
        return self.agent.run(input_data, state=context)
