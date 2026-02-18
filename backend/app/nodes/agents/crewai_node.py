"""
CrewAI Node - Studio Standard (Universal Method)
Batch 114: Advanced AI Frameworks & Memory
"""
from typing import Any, Dict, Optional, List
from ..base import BaseNode
from ..registry import register_node

@register_node("crewai_agent_node")
class CrewAIAgentNode(BaseNode):
    """
    Create and execute a CrewAI Agent.
    """
    node_type = "crewai_agent_node"
    version = "1.0.0"
    category = "agents"
    credentials_required = []


    properties = [
        {
            'displayName': 'Allow Delegation',
            'name': 'allow_delegation',
            'type': 'boolean',
            'default': True,
        },
        {
            'displayName': 'Backstory',
            'name': 'backstory',
            'type': 'string',
            'default': '',
            'required': True,
        },
        {
            'displayName': 'Goal',
            'name': 'goal',
            'type': 'string',
            'default': '',
            'required': True,
        },
        {
            'displayName': 'Role',
            'name': 'role',
            'type': 'string',
            'default': '',
            'required': True,
        },
        {
            'displayName': 'Verbose',
            'name': 'verbose',
            'type': 'boolean',
            'default': True,
        },
    ]
    inputs = {
        "role": {"type": "string", "required": True},
        "goal": {"type": "string", "required": True},
        "backstory": {"type": "string", "required": True},
        "allow_delegation": {"type": "boolean", "default": True},
        "verbose": {"type": "boolean", "default": True}
    }

    outputs = {
        "agent": {"type": "any"},
        "status": {"type": "string"}
    }

    async def execute(self, input_data: Any, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        try:
            from crewai import Agent
        except ImportError:
            return {"status": "error", "error": "crewai not installed"}

        try:
            agent = Agent(
                role=self.get_config("role"),
                goal=self.get_config("goal"),
                backstory=self.get_config("backstory"),
                allow_delegation=self.get_config("allow_delegation", True),
                verbose=self.get_config("verbose", True)
            )
            return {
                "status": "success",
                "data": {
                    "agent": agent
                }
            }
        except Exception as e:
            return {"status": "error", "error": f"CrewAI Agent Creation Failed: {str(e)}"}