import json
from typing import Any, Dict, Optional, List
from ..base import BaseNode
from ..registry import register_node
import re

@register_node("conditional_branch")
class ConditionalBranchNode(BaseNode):
    """
    Routes workflows based on conditions (If/Else).
    Outputs to 'true_result' or 'false_result' handles.
    """
    node_type = "conditional_branch"
    version = "1.0.0"
    category = "logic"

    inputs = {
        "value_a": {"type": "string", "description": "Left side of comparison"},
        "operator": {
            "type": "string", 
            "enum": ["equals", "contains", "regex", "exists"],
            "default": "equals"
        },
        "value_b": {"type": "string", "description": "Right side of comparison"},
        "case_sensitive": {"type": "boolean", "default": True}
    }
    outputs = {
        "true_result": {"type": "any"},
        "false_result": {"type": "any"},
        "status": {"type": "string"}
    }

    async def execute(self, input_data: Any, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        val_a = str(input_data) if input_data is not None else self.get_config("value_a", "")
        if isinstance(input_data, dict):
            val_a = input_data.get("value") or input_data.get("text") or val_a
        
        op = self.get_config("operator", "equals")
        val_b = self.get_config("value_b", "")
        case_sensitive = self.get_config("case_sensitive", True)

        if not case_sensitive:
            val_a = str(val_a).lower()
            val_b = str(val_b).lower()
        
        result = False
        if op == "equals":
            result = str(val_a) == str(val_b)
        elif op == "contains":
            result = str(val_b) in str(val_a)
        elif op == "regex":
            result = bool(re.search(str(val_b), str(val_a)))
        elif op == "exists":
            result = bool(val_a)

        # We return the data on the specific handle the engine expects
        handle = "true_result" if result else "false_result"
        return {
            "status": "success",
            "data": input_data, # Default data
            handle: input_data  # Explicit handle matching for engine
        }

@register_node("task_sequencer")
class TaskSequencerNode(BaseNode):
    """
    A pass-through node used to explicitly sequence tasks or aggregate data.
    """
    node_type = "task_sequencer"
    version = "1.0.0"
    category = "logic"

    inputs = {
        "input": {"type": "any"}
    }
    outputs = {
        "output": {"type": "any"},
        "status": {"type": "string"}
    }

    async def execute(self, input_data: Any, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        return {
            "status": "success",
            "data": input_data
        }

@register_node("autonomous_agent_v2")
class AutonomousAgentNodeV2(BaseNode):
    """
    Enhanced Autonomous Agent with Node Law compliance.
    """
    node_type = "autonomous_agent_v2"
    version = "2.0.0"
    category = "agents"

    async def execute(self, input_data: Any, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        # Implementation logic from autonomous_agent.py but with Node Law output
        from .autonomous_agent import AutonomousAgentNode
        legacy = AutonomousAgentNode(config=self.config)
        res = await legacy.execute(input_data, context)
        
        if isinstance(res, dict) and "error" in res:
            return {"status": "error", "error": res["error"]}
        
        return {
            "status": "success",
            "data": res
        }
