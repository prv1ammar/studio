"""
Wait Node - Studio Standard (Universal Method)
Batch 103: Core Workflow Nodes
"""
from typing import Any, Dict, Optional
import asyncio
from datetime import datetime, timedelta
from ..base import BaseNode
from ..registry import register_node

@register_node("wait_node")
class WaitNode(BaseNode):
    """
    Pause workflow execution for a specified duration or until a specific time.
    """
    node_type = "wait_node"
    version = "1.0.0"
    category = "flow_controls"
    credentials_required = []


    properties = [
        {
            'displayName': 'Duration',
            'name': 'duration',
            'type': 'string',
            'default': 1,
            'description': 'Duration to wait',
        },
        {
            'displayName': 'Mode',
            'name': 'mode',
            'type': 'options',
            'default': 'duration',
            'options': [
                {'name': 'Duration', 'value': 'duration'},
                {'name': 'Until Time', 'value': 'until_time'},
                {'name': 'Until Date', 'value': 'until_date'},
            ],
            'description': 'Wait mode',
        },
        {
            'displayName': 'Unit',
            'name': 'unit',
            'type': 'options',
            'default': 'seconds',
            'options': [
                {'name': 'Seconds', 'value': 'seconds'},
                {'name': 'Minutes', 'value': 'minutes'},
                {'name': 'Hours', 'value': 'hours'},
                {'name': 'Days', 'value': 'days'},
            ],
            'description': 'Time unit',
        },
        {
            'displayName': 'Until Date',
            'name': 'until_date',
            'type': 'string',
            'default': '',
            'description': 'Wait until this date (YYYY-MM-DD HH:MM format)',
        },
        {
            'displayName': 'Until Time',
            'name': 'until_time',
            'type': 'string',
            'default': '',
            'description': 'Wait until this time (HH:MM format)',
        },
    ]
    inputs = {
        "mode": {
            "type": "dropdown",
            "default": "duration",
            "options": ["duration", "until_time", "until_date"],
            "description": "Wait mode"
        },
        "duration": {
            "type": "number",
            "default": 1,
            "optional": True,
            "description": "Duration to wait"
        },
        "unit": {
            "type": "dropdown",
            "default": "seconds",
            "options": ["seconds", "minutes", "hours", "days"],
            "optional": True,
            "description": "Time unit"
        },
        "until_time": {
            "type": "string",
            "optional": True,
            "description": "Wait until this time (HH:MM format)"
        },
        "until_date": {
            "type": "string",
            "optional": True,
            "description": "Wait until this date (YYYY-MM-DD HH:MM format)"
        }
    }

    outputs = {
        "result": {"type": "any"},
        "status": {"type": "string"},
        "wait_info": {"type": "object"}
    }

    async def execute(self, input_data: Any, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        try:
            mode = self.get_config("mode", "duration")
            
            wait_seconds = 0
            wait_until = None
            
            if mode == "duration":
                duration = float(self.get_config("duration", 1))
                unit = self.get_config("unit", "seconds")
                
                # Convert to seconds
                if unit == "minutes":
                    wait_seconds = duration * 60
                elif unit == "hours":
                    wait_seconds = duration * 3600
                elif unit == "days":
                    wait_seconds = duration * 86400
                else:  # seconds
                    wait_seconds = duration
                
                # Perform the wait
                await asyncio.sleep(wait_seconds)
                
                return {
                    "status": "success",
                    "data": {
                        "result": input_data,
                        "wait_info": {
                            "mode": "duration",
                            "waited_seconds": wait_seconds,
                            "waited_duration": f"{duration} {unit}"
                        }
                    }
                }
            
            elif mode == "until_time":
                until_time_str = self.get_config("until_time", "00:00")
                
                try:
                    # Parse time (HH:MM format)
                    target_hour, target_minute = map(int, until_time_str.split(":"))
                    
                    now = datetime.now()
                    target_time = now.replace(hour=target_hour, minute=target_minute, second=0, microsecond=0)
                    
                    # If target time is in the past today, set it for tomorrow
                    if target_time <= now:
                        target_time += timedelta(days=1)
                    
                    wait_seconds = (target_time - now).total_seconds()
                    
                    # Cap wait time at 24 hours for safety
                    if wait_seconds > 86400:
                        wait_seconds = 86400
                    
                    await asyncio.sleep(wait_seconds)
                    
                    return {
                        "status": "success",
                        "data": {
                            "result": input_data,
                            "wait_info": {
                                "mode": "until_time",
                                "target_time": target_time.isoformat(),
                                "waited_seconds": wait_seconds
                            }
                        }
                    }
                
                except ValueError:
                    return {"status": "error", "error": "Invalid time format. Use HH:MM"}
            
            elif mode == "until_date":
                until_date_str = self.get_config("until_date")
                
                if not until_date_str:
                    return {"status": "error", "error": "until_date required for this mode"}
                
                try:
                    # Parse datetime (YYYY-MM-DD HH:MM format)
                    target_datetime = datetime.fromisoformat(until_date_str.replace(" ", "T"))
                    
                    now = datetime.now()
                    
                    if target_datetime <= now:
                        return {
                            "status": "success",
                            "data": {
                                "result": input_data,
                                "wait_info": {
                                    "mode": "until_date",
                                    "message": "Target date/time is in the past, continuing immediately"
                                }
                            }
                        }
                    
                    wait_seconds = (target_datetime - now).total_seconds()
                    
                    # Cap wait time at 7 days for safety
                    if wait_seconds > 604800:
                        wait_seconds = 604800
                    
                    await asyncio.sleep(wait_seconds)
                    
                    return {
                        "status": "success",
                        "data": {
                            "result": input_data,
                            "wait_info": {
                                "mode": "until_date",
                                "target_datetime": target_datetime.isoformat(),
                                "waited_seconds": wait_seconds
                            }
                        }
                    }
                
                except ValueError:
                    return {"status": "error", "error": "Invalid date format. Use YYYY-MM-DD HH:MM"}
            
            return {"status": "error", "error": f"Unsupported wait mode: {mode}"}

        except Exception as e:
            return {"status": "error", "error": f"Wait Node Failed: {str(e)}"}