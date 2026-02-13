from typing import Any, Dict, Optional, List
from ..base import BaseNode
from ..registry import register_node
import json

@register_node("analytics_action")
class AnalyticsNode(BaseNode):
    """
    Unified Node for Analytics and Monitoring (Mixpanel, BTRIX, Sentry).
    """
    node_type = "analytics_action"
    version = "1.0.0"
    category = "integrations"
    credentials_required = ["analytics_auth"]

    inputs = {
        "service": {"type": "string", "default": "btrix", "enum": ["btrix", "mixpanel", "sentry", "google_analytics"]},
        "action": {"type": "string", "default": "fetch_metrics", "enum": ["fetch_metrics", "track_event", "log_error", "generate_report"]},
        "event_name": {"type": "string", "optional": True},
        "properties": {"type": "object", "optional": True}
    }
    outputs = {
        "results": {"type": "any"},
        "status": {"type": "string"}
    }

    async def execute(self, input_data: Any, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        try:
            # 1. Resolve Auth
            creds = await self.get_credential("analytics_auth")
            api_key = creds.get("api_key") or self.get_config("api_key")
            
            service = self.get_config("service", "btrix")
            action = self.get_config("action", "fetch_metrics")

            # Simulation for standardized output
            if service == "btrix":
                if action == "fetch_metrics":
                    return {
                        "status": "success",
                        "data": {
                            "metrics": {"active_users": 1250, "retention_rate": 0.34, "revenue": 4500.0}
                        }
                    }
                elif action == "generate_report":
                    return {
                        "status": "success",
                        "data": {"report_url": "https://analytics.btrix.io/reports/rpt_123"}
                    }
            
            elif service == "mixpanel":
                # Simulated Mixpanel Tracking
                event = self.get_config("event_name") or str(input_data)
                return {
                    "status": "success",
                    "data": {"event": event, "status": "tracked"}
                }

            elif service == "sentry":
                # Simulated Sentry Error Logging
                error_msg = str(input_data)
                return {
                    "status": "success",
                    "data": {"issue_id": "SENTRY-456", "level": "error"}
                }

            return {"status": "error", "error": f"Unsupported Analytics service/action: {service}/{action}"}

        except Exception as e:
            return {"status": "error", "error": f"Analytics Node Error: {str(e)}"}
