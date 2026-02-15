"""
Google Analytics Node - Studio Standard (Universal Method)
Batch 109: Analytics & Support
"""
from typing import Any, Dict, Optional
import aiohttp
from ...base import BaseNode
from ...registry import register_node

@register_node("google_analytics_node")
class GoogleAnalyticsNode(BaseNode):
    """
    Google Analytics 4 (GA4) integration.
    """
    node_type = "google_analytics_node"
    version = "1.0.0"
    category = "analytics"
    credentials_required = ["google_analytics_auth"]

    inputs = {
        "action": {
            "type": "dropdown",
            "default": "run_report",
            "options": ["run_report", "get_metadata"],
            "description": "GA4 action"
        },
        "property_id": {
            "type": "string",
            "optional": True,
            "description": "GA4 Property ID"
        },
        "date_ranges": {
            "type": "string",
            "optional": True,
            "description": "JSON list of date ranges"
        },
        "dimensions": {
            "type": "string",
            "optional": True,
            "description": "Comma separated dimensions"
        },
        "metrics": {
            "type": "string",
            "optional": True,
            "description": "Comma separated metrics"
        }
    }

    outputs = {
        "result": {"type": "any"},
        "status": {"type": "string"}
    }

    async def execute(self, input_data: Any, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        try:
            creds = await self.get_credential("google_analytics_auth")
            access_token = creds.get("access_token")
            
            if not access_token:
                return {"status": "error", "error": "Google Analytics access token required"}

            base_url = "https://analyticsdata.googleapis.com/v1beta"
            headers = {"Authorization": f"Bearer {access_token}", "Content-Type": "application/json"}
            
            action = self.get_config("action", "run_report")

            async with aiohttp.ClientSession() as session:
                if action == "run_report":
                    property_id = self.get_config("property_id")
                    if not property_id:
                        return {"status": "error", "error": "property_id required"}
                        
                    url = f"{base_url}/properties/{property_id}:runReport"
                    
                    # Construct request body
                    payload = {}
                    
                    # Date Ranges
                    dr_str = self.get_config("date_ranges")
                    if dr_str:
                         import json
                         try:
                             payload["dateRanges"] = json.loads(dr_str)
                         except:
                             payload["dateRanges"] = [{"startDate": "30daysAgo", "endDate": "today"}]
                    else:
                        payload["dateRanges"] = [{"startDate": "30daysAgo", "endDate": "today"}]
                        
                    # Dimensions
                    dims = self.get_config("dimensions")
                    if dims:
                        payload["dimensions"] = [{"name": d.strip()} for d in dims.split(",") if d.strip()]
                        
                    # Metrics
                    mets = self.get_config("metrics")
                    if mets:
                        payload["metrics"] = [{"name": m.strip()} for m in mets.split(",") if m.strip()]
                    else:
                        payload["metrics"] = [{"name": "activeUsers"}] # Default
                        
                    async with session.post(url, headers=headers, json=payload) as resp:
                         if resp.status != 200:
                            error_text = await resp.text()
                            return {"status": "error", "error": f"GA4 API Error {resp.status}: {error_text}"}
                         res_data = await resp.json()
                         return {"status": "success", "data": {"result": res_data}}

                elif action == "get_metadata":
                    # Admin API typically separate, simplified here or placeholder
                    return {"status": "error", "error": "Metadata retrieval requires Admin API scope"}

            return {"status": "error", "error": f"Unsupported action: {action}"}

        except Exception as e:
            return {"status": "error", "error": f"Google Analytics Node Failed: {str(e)}"}
