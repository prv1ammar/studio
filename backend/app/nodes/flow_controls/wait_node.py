"""
Wait Node - Studio Standard (Universal Method)
Batch 93: Advanced Workflow (n8n Critical)
"""
from typing import Any, Dict, Optional, List
import asyncio
from datetime import datetime
from ...base import BaseNode
from ...registry import register_node

@register_node("wait_node")
class WaitNode(BaseNode):
    """
    Pause execution for a specific duration or until a trigger.
    """
    node_type = "wait_node"
    version = "1.0.0"
    category = "flow_control"
    credentials_required = []

    inputs = {
        "mode": {
            "type": "dropdown",
            "default": "wait_amount",
            "options": ["wait_amount", "wait_until"],
            "description": "Wait mode"
        },
        "amount": {
            "type": "number",
            "description": "Amount of time to wait"
        },
        "unit": {
            "type": "dropdown",
            "default": "seconds",
            "options": ["seconds", "minutes", "hours", "days"],
            "description": "Time unit"
        },
        "date_time": {
            "type": "string",
            "description": "Specific date/time to wait until (ISO 8601)"
        }
    }

    outputs = {
        "result": {"type": "any"},
        "status": {"type": "string"}
    }

    async def execute(self, input_data: Any, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        try:
            mode = self.get_config("mode", "wait_amount")
            
            if mode == "wait_amount":
                amount = float(self.get_config("amount", 1))
                unit = self.get_config("unit", "seconds")
                
                seconds = amount
                if unit == "minutes":
                    seconds *= 60
                elif unit == "hours":
                    seconds *= 3600
                elif unit == "days":
                    seconds *= 86400
                
                # In execution engine, we perform the wait
                await asyncio.sleep(seconds)
                
                return {
                    "status": "success",
                    "data": {
                        "result": input_data,
                        "waited_seconds": seconds
                    }
                }
            
            elif mode == "wait_until":
                date_str = self.get_config("date_time")
                if not date_str:
                    return {"status": "error", "error": "date_time required for wait_until"}
                
                target_time = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
                now = datetime.now(target_time.tzinfo)
                
                wait_seconds = (target_time - now).total_seconds()
                
                if wait_seconds > 0:
                    await asyncio.sleep(wait_seconds)
                
                return {
                    "status": "success",
                    "data": {
                        "result": input_data,
                        "waited_until": date_str
                    }
                }
            
            return {"status": "error", "error": f"Unsupported mode: {mode}"}

        except Exception as e:
            return {"status": "error", "error": f"Wait Node Failed: {str(e)}"}
