from ...base import BaseNode
from ...registry import register_node
from typing import Any, Dict, Optional

@register_node("chatOutput")
class ChatOutputNode(BaseNode):
    async def execute(self, input_data: Any, context: Optional[Dict[str, Any]] = None) -> Any:
        # ChatOutput returns the final result
        return str(input_data)
