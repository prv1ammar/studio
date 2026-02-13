"""
Google Analytics 4 (GA4) Node - Studio Standard (Universal Method)
Batch 98: Analytics (Enterprise Expansion)
"""
from typing import Any, Dict, Optional, List
import aiohttp
from ...base import BaseNode
from ...registry import register_node

@register_node("google_analytics_node")
class GoogleAnalyticsNode(BaseNode):
    """
    Report data and track events via Google Analytics 4 (GA4) Data API and Measurement Protocol.
    """
    node_type = "google_analytics_node"
    version = "1.0.0"
    category = "analytics"
    credentials_required = ["google_analytics_auth"]

    inputs = {
        "action": {
            "type": "dropdown",
            "default": "run_report",
            "options": ["run_report", "send_event"],
            "description": "GA4 action"
        },
        "property_id": {
            "type": "string",
            "description": "GA4 Property ID"
        },
        "date_ranges": {
            "type": "string",
            "optional": True,
            "description": "Date ranges (e.g. yesterday, today, 2023-01-01 to 2023-01-31)"
        },
        "dimensions": {
            "type": "string",
            "optional": True,
            "description": "Comma-separated dimensions (e.g. city, eventName)"
        },
        "metrics": {
            "type": "string",
            "optional": True,
            "description": "Comma-separated metrics (e.g. activeUsers, eventCount)"
        },
        "event_name": {
            "type": "string",
            "optional": True,
            "description": "Event name for measurement protocol"
        },
        "event_params": {
             "type": "string",
             "optional": True,
             "description": "JSON event parameters"
        },
        "client_id": {
            "type": "string",
            "optional": True,
            "description": "Client ID for user tracking"
        }
    }

    outputs = {
        "result": {"type": "any"},
        "status": {"type": "string"}
    }

    async def execute(self, input_data: Any, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        try:
            # 1. Authentication
            creds = await self.get_credential("google_analytics_auth")
            access_token = creds.get("access_token") # OAuth token for Data API
            api_secret = creds.get("api_secret") # For Measurement Protocol
            measurement_id = creds.get("measurement_id") # For Measurement Protocol
            
            action = self.get_config("action", "run_report")

            async with aiohttp.ClientSession() as session:
                
                # Reporting (Data API)
                if action == "run_report":
                    if not access_token:
                        return {"status": "error", "error": "Google Access Token required for reporting."}
                    
                    property_id = self.get_config("property_id")
                    if not property_id:
                        return {"status": "error", "error": "property_id required"}

                    # Construct JSON payload
                    # This is simplified; robust implementation would parse ranges/dims/metrics more fully
                    date_range_str = self.get_config("date_ranges", "yesterday")
                    start_date = date_range_str
                    end_date = date_range_str # Simple default
                    if " to " in date_range_str:
                         start_date, end_date = date_range_str.split(" to ")

                    dims = [{"name": d.strip()} for d in self.get_config("dimensions", "").split(",") if d.strip()]
                    metrics = [{"name": m.strip()} for m in self.get_config("metrics", "").split(",") if m.strip()]

                    payload = {
                        "dateRanges": [{"startDate": start_date, "endDate": end_date}],
                        "dimensions": dims,
                        "metrics": metrics
                    }

                    url = f"https://analyticsdata.googleapis.com/v1beta/properties/{property_id}:runReport"
                    headers = {
                        "Authorization": f"Bearer {access_token}",
                        "Content-Type": "application/json"
                    }

                    async with session.post(url, headers=headers, json=payload) as resp:
                        if resp.status != 200:
                            return {"status": "error", "error": f"GA4 API Error: {resp.status}"}
                        res_data = await resp.json()
                        return {"status": "success", "data": {"result": res_data}}

                # Tracking (Measurement Protocol)
                elif action == "send_event":
                    if not api_secret or not measurement_id:
                        return {"status": "error", "error": "API Secret and Measurement ID required for sending events."}
                    
                    event_name = self.get_config("event_name")
                    client_id = self.get_config("client_id", "555555555.555555555") # Dummy default if not provided
                    
                    if not event_name:
                        return {"status": "error", "error": "event_name required"}

                    import json
                    params_str = self.get_config("event_params")
                    params = {}
                    if params_str:
                        params = json.loads(params_str) if isinstance(params_str, str) else params_str

                    payload = {
                        "client_id": client_id,
                        "events": [{
                            "name": event_name,
                            "params": params
                        }]
                    }
                    
                    url = f"https://www.google-analytics.com/mp/collect?measurement_id={measurement_id}&api_secret={api_secret}"
                    
                    async with session.post(url, json=payload) as resp:
                         # 204 No Content is success for MP
                         if resp.status not in [200, 204]:
                              return {"status": "error", "error": f"Measurement Protocol Error: {resp.status}"}
                         return {"status": "success", "data": {"result": {"message": "Event sent"}}}

                return {"status": "error", "error": f"Unsupported action: {action}"}

        except Exception as e:
            return {"status": "error", "error": f"Google Analytics Node Failed: {str(e)}"}
