"""
Sentry Monitoring Node - Studio Standard
Batch 49: Analytics & Monitoring
"""
from typing import Any, Dict, Optional
import aiohttp
from ...base import BaseNode
from ...registry import register_node

@register_node("sentry_node")
class SentryNode(BaseNode):
    """
    Log events and exceptions to Sentry.
    """
    node_type = "sentry_node"
    version = "1.0.0"
    category = "analytics"
    credentials_required = ["sentry_auth"]

    inputs = {
        "level": {
            "type": "dropdown",
            "default": "error",
            "options": ["error", "warning", "info", "debug"],
            "description": "Log level"
        },
        "message": {
            "type": "string",
            "required": True,
            "description": "Error or log message"
        },
        "extra_data": {
            "type": "json",
            "optional": True,
            "description": "Contextual data for the event"
        },
        "dsn": {
            "type": "string",
            "description": "Sentry DSN (if not in credentials)"
        }
    }

    outputs = {
        "status": {"type": "string"},
        "event_id": {"type": "string"}
    }

    async def execute(self, input_data: Any, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        try:
            import sentry_sdk
        except ImportError:
            return {"status": "error", "error": "sentry-sdk not installed. Run: pip install sentry-sdk"}

        try:
            # 1. Resolve Auth/DSN
            creds = await self.get_credential("sentry_auth")
            dsn = creds.get("dsn") if creds else self.get_config("dsn")
            
            if not dsn:
                return {"status": "error", "error": "Sentry DSN is required."}

            msg = self.get_config("message")
            if isinstance(input_data, str) and input_data:
                msg = input_data
            elif isinstance(input_data, Exception):
                msg = str(input_data)
            
            if not msg:
                 return {"status": "error", "error": "Message is required."}

            level = self.get_config("level", "error")
            extra = self.get_config("extra_data", {})
            if isinstance(input_data, dict):
                extra.update(input_data)

            # Sentry SDK is usually global, but we can capture individual messages
            # If not initialized, initialize it for this call (scoped)
            with sentry_sdk.init(dsn=dsn):
                with sentry_sdk.push_scope() as scope:
                    for key, val in extra.items():
                        scope.set_extra(key, val)
                    
                    event_id = sentry_sdk.capture_message(msg, level=level)
            
            return {
                "status": "success",
                "data": {
                    "event_id": event_id,
                    "level": level,
                    "status": "logged"
                }
            }

        except Exception as e:
            return {"status": "error", "error": f"Sentry Node Failed: {str(e)}"}
