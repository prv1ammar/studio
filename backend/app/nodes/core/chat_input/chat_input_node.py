from ...base import BaseNode
from ...registry import register_node
from typing import Any, Dict, Optional

@register_node("chatInput")
class ChatInputNode(BaseNode):
    async def execute(self, input_data: Any, context: Optional[Dict[str, Any]] = None) -> Any:
        # ChatInput simply passes through the user message
        return input_data
