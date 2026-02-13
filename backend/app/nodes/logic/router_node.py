"""
Router Logic Node - Studio Standard
Batch 38: Logic & Flow Control
"""
import re
from typing import Any, Dict, Optional, List
from ...base import BaseNode
from ...registry import register_node

@register_node("router")
class RouterNode(BaseNode):
    """
    Routes an input to one of multiple outputs based on rules.
    Ideal for classifying intent (e.g., 'greeting', 'complaint', 'query').
    """
    node_type = "router"
    version = "1.0.0"
    category = "logic"
    credentials_required = []

    inputs = {
        "input_text": {
            "type": "string",
            "required": True,
            "description": "Text to route"
        },
        "routes": {
            "type": "json",
            "default": [
                {"name": "route1", "condition": "contains", "match": "hello"},
                {"name": "route2", "condition": "regex", "match": "^error.*"}
            ],
            "description": "List of route definitions"
        },
        "default_route": {
            "type": "string",
            "default": "default",
            "description": "Default route name if no match found"
        }
    }

    outputs = {
        "output": {"type": "string"},
        "route_name": {"type": "string"},
        "full_match": {"type": "object"}
    }
    
    # Dynamic outputs are supported in Studio via additional metadata usually, 
    # but fixed schema is safer for now.

    async def execute(self, input_data: Any, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        try:
            # Get input
            text = input_data if isinstance(input_data, str) else self.get_config("input_text", "")
            
            # Get routes configuration
            routes = self.get_config("routes", [])
            default_route = self.get_config("default_route", "default")

            if not text:
                return {"status": "error", "error": "Input text required"}

            matched_route = None

            # Iterate through routes
            for route in routes:
                name = route.get("name")
                condition = route.get("condition", "contains")
                match_val = route.get("match", "")
                
                if self._check_condition(text, condition, match_val):
                    matched_route = name
                    break
            
            # Use default if no match
            if not matched_route:
                matched_route = default_route

            # Return result
            return {
                "status": "success",
                "data": {
                    "output": text,
                    "route_name": matched_route,
                    "full_match": {
                        "text": text,
                        "route": matched_route
                    }
                }
            }

        except Exception as e:
            return {
                "status": "error",
                "error": f"Router failed: {str(e)}"
            }

    def _check_condition(self, text: str, condition: str, match_val: str) -> bool:
        text = str(text).lower()
        match_val = str(match_val).lower()

        if condition == "contains":
            return match_val in text
        elif condition == "equals":
            return text == match_val
        elif condition == "starts with":
            return text.startswith(match_val)
        elif condition == "ends with":
            return text.endswith(match_val)
        elif condition == "regex":
            try:
                return bool(re.search(match_val, text))
            except:
                return False
        return False
