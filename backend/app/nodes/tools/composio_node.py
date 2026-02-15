"""
Composio Node - Studio Standard (Universal Method)
Batch 116: Specialized Toolkits
"""
from typing import Any, Dict, Optional, List
from ...base import BaseNode
from ...registry import register_node

@register_node("composio_node")
class ComposioNode(BaseNode):
    """
    Connect agents to 100+ tools using Composio.
    """
    node_type = "composio_node"
    version = "1.0.0"
    category = "tools"
    credentials_required = ["composio_auth"]

    inputs = {
        "action_name": {
            "type": "string",
            "required": True,
            "description": "Composio action name (e.g., github_create_issue)"
        },
        "parameters": {
            "type": "json",
            "default": "{}",
            "description": "Parameters for the action"
        },
        "entity_id": {
            "type": "string",
            "default": "default"
        }
    }

    outputs = {
        "result": {"type": "any"},
        "status": {"type": "string"}
    }

    async def execute(self, input_data: Any, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        try:
            from composio import Composio
        except ImportError:
            return {"status": "error", "error": "composio-core not installed"}

        try:
            creds = await self.get_credential("composio_auth")
            api_key = creds.get("api_key")
            
            if not api_key:
                return {"status": "error", "error": "Composio API Key is required"}

            client = Composio(api_key=api_key)
            action = self.get_config("action_name")
            params = self.get_config("parameters", {})
            
            if isinstance(params, str):
                import json
                params = json.loads(params)
            
            if isinstance(input_data, dict):
                params.update(input_data)

            res = client.execute_action(
                action=action,
                params=params,
                entity_id=self.get_config("entity_id", "default")
            )
            
            return {
                "status": "success",
                "data": {
                    "result": res
                }
            }

        except Exception as e:
            return {"status": "error", "error": f"Composio execution failed: {str(e)}"}
