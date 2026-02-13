"""
Mixpanel Node - Studio Standard (Universal Method)
Batch 98: Analytics (Enterprise Expansion)
"""
from typing import Any, Dict, Optional, List
import aiohttp
import base64
from ...base import BaseNode
from ...registry import register_node

@register_node("mixpanel_node")
class MixpanelNode(BaseNode):
    """
    Track events, engage users, and query data via Mixpanel API.
    """
    node_type = "mixpanel_node"
    version = "1.0.0"
    category = "analytics"
    credentials_required = ["mixpanel_auth"]

    inputs = {
        "action": {
            "type": "dropdown",
            "default": "track_event",
            "options": ["track_event", "engage_user", "query_jql", "query_raw"],
            "description": "Mixpanel action"
        },
        "event_name": {
            "type": "string",
            "optional": True
        },
        "properties": {
            "type": "string",
            "optional": True,
            "description": "JSON properties"
        },
        "distinct_id": {
            "type": "string",
            "optional": True,
            "description": "User Distinct ID"
        },
        "query": {
            "type": "string",
            "optional": True,
            "description": "JQL script or query"
        }
    }

    outputs = {
        "result": {"type": "any"},
        "status": {"type": "string"}
    }

    async def execute(self, input_data: Any, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        try:
            # 1. Authentication
            creds = await self.get_credential("mixpanel_auth")
            project_token = creds.get("project_token")
            api_secret = creds.get("api_secret") # Needed for querying
            
            if not project_token:
                return {"status": "error", "error": "Mixpanel Project Token required."}

            action = self.get_config("action", "track_event")
            
            # Base URLs
            ingestion_url = "https://api.mixpanel.com"
            query_url = "https://mixpanel.com/api/2.0" # Legacy query API usage, or new endpoints as needed

            async with aiohttp.ClientSession() as session:
                
                if action == "track_event":
                    event = self.get_config("event_name")
                    if not event:
                        return {"status": "error", "error": "event_name required"}
                    
                    import json
                    props_str = self.get_config("properties")
                    props = {}
                    if props_str:
                         props = json.loads(props_str) if isinstance(props_str, str) else props_str
                    
                    # Ensure token
                    if "token" not in props:
                        props["token"] = project_token
                    
                    # Build event object
                    payload = [{
                        "event": event,
                        "properties": props
                    }]
                    
                    # Track endpoint accepts base64 encoded JSON data parameter or JSON body
                    # Using JSON body (easier) if supported, else data parameter
                    # The official `track` endpoint often uses `data=` parameter with base64 encoded JSON
                    
                    data_str = json.dumps(payload)
                    b64_data = base64.b64encode(data_str.encode()).decode()
                    
                    track_url = f"{ingestion_url}/track"
                    params = {"data": b64_data}
                    
                    async with session.get(track_url, params=params) as resp:
                         text = await resp.text()
                         # 1 means success, 0 typically failure
                         if text == "1":
                              return {"status": "success", "data": {"result": {"status": "Event tracked"}}}
                         else:
                              return {"status": "error", "error": f"Mixpanel: {text}"}

                elif action == "engage_user":
                     # Create/Update profile
                     distinct_id = self.get_config("distinct_id")
                     if not distinct_id:
                          return {"status": "error", "error": "distinct_id required"}
                          
                     import json
                     props_str = self.get_config("properties")
                     props = {}
                     if props_str:
                          props = json.loads(props_str) if isinstance(props_str, str) else props_str

                     payload = [{
                          "$token": project_token,
                          "$distinct_id": distinct_id,
                          "$set": props
                     }]
                     
                     data_str = json.dumps(payload)
                     b64_data = base64.b64encode(data_str.encode()).decode()
                     
                     engage_url = f"{ingestion_url}/engage"
                     params = {"data": b64_data}
                     
                     async with session.get(engage_url, params=params) as resp:
                          text = await resp.text()
                          if text == "1":
                               return {"status": "success", "data": {"result": {"status": "Profile updated"}}}
                          else:
                               return {"status": "error", "error": f"Mixpanel: {text}"}

                elif action == "query_jql":
                     if not api_secret:
                          return {"status": "error", "error": "API Secret required for JQL querying"}
                     
                     jql_script = self.get_config("query")
                     if not jql_script:
                          return {"status": "error", "error": "query (JQL script) required"}
                     
                     url = f"{query_url}/jql"
                     # Basic Auth with API Secret
                     auth = aiohttp.BasicAuth(api_secret, "")
                     data = {"script": jql_script}
                     
                     async with session.post(url, auth=auth, data=data) as resp:
                          if resp.status != 200:
                               return {"status": "error", "error": f"Mixpanel API Error: {resp.status}"}
                          res_data = await resp.json()
                          return {"status": "success", "data": {"result": res_data}}

                return {"status": "error", "error": f"Unsupported action: {action}"}

        except Exception as e:
            return {"status": "error", "error": f"Mixpanel Node Failed: {str(e)}"}
