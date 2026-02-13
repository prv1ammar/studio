"""
HTTP Request Node - Studio Standard (Universal Method)
Batch 99: Web & Utilities (Deepening Parity)
"""
from typing import Any, Dict, Optional, List
import aiohttp
import json
from ...base import BaseNode
from ...registry import register_node

@register_node("http_request_node")
class HTTPRequestNode(BaseNode):
    """
    Make HTTP requests to any URL (The Swiss Army Knife of Nodes).
    """
    node_type = "http_request_node"
    version = "1.0.0"
    category = "utilities"
    credentials_required = [] # Auth can be passed in headers/auth inputs or generic creds

    inputs = {
        "method": {
            "type": "dropdown",
            "default": "GET",
            "options": ["GET", "POST", "PUT", "PATCH", "DELETE", "HEAD"],
            "description": "HTTP Method"
        },
        "url": {
            "type": "string",
            "required": True,
            "description": "Target URL"
        },
        "headers": {
            "type": "string",
            "optional": True,
            "description": "JSON headers"
        },
        "body_content_type": {
             "type": "dropdown",
             "default": "json",
             "options": ["json", "form-data", "x-www-form-urlencoded", "raw"],
             "description": "Body Content Type"
        },
        "body": {
            "type": "string",
            "optional": True,
            "description": "Request Body (JSON or string)"
        },
        "authentication": {
            "type": "dropdown",
            "default": "none",
            "options": ["none", "basic", "bearer", "header"],
            "optional": True
        }
        # Simplified auth inputs for ad-hoc requests
    }

    outputs = {
        "result": {"type": "any"},
        "status": {"type": "string"},
        "headers": {"type": "any"},
        "status_code": {"type": "number"}
    }

    async def execute(self, input_data: Any, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        try:
            method = self.get_config("method", "GET")
            url = self.get_config("url")
            
            if not url:
                return {"status": "error", "error": "url required"}
            
            # Headers
            headers_str = self.get_config("headers", "{}")
            headers = json.loads(headers_str) if isinstance(headers_str, str) else headers_str
            
            # Body
            body_type = self.get_config("body_content_type", "json")
            body_input = self.get_config("body")
            
            data = None
            json_data = None
            
            if body_input:
                if body_type == "json":
                    try:
                        json_data = json.loads(body_input) if isinstance(body_input, str) else body_input
                    except:
                        json_data = body_input # Fallback
                elif body_type == "x-www-form-urlencoded":
                    data = body_input # aiohttp handles dict or str
                    if isinstance(body_input, str):
                        try:
                             # Try parsing if it looks like json dict
                             data = json.loads(body_input)
                        except:
                             pass
                    if "Content-Type" not in headers:
                        headers["Content-Type"] = "application/x-www-form-urlencoded"
                elif body_type == "raw":
                    data = body_input
                # form-data is complex with aiohttp in this generic context, skipping for brevity or treating as raw/dict
            
            async with aiohttp.ClientSession() as session:
                response = None
                
                # Simple Auth handling (Basic/Bearer can be added to headers)
                # In robust version, we'd use BaseNode.get_credential or specific inputs
                # This basic version assumes header auth is manually added or no auth
                
                if method == "GET":
                    response = await session.get(url, headers=headers)
                elif method == "POST":
                    response = await session.post(url, headers=headers, json=json_data, data=data)
                elif method == "PUT":
                    response = await session.put(url, headers=headers, json=json_data, data=data)
                elif method == "PATCH":
                    response = await session.patch(url, headers=headers, json=json_data, data=data)
                elif method == "DELETE":
                    response = await session.delete(url, headers=headers, json=json_data, data=data)
                
                if response:
                    async with response:
                        status_code = response.status
                        res_headers = dict(response.headers)
                        
                        # Try to parse JSON, fall back to text
                        try:
                            res_data = await response.json()
                        except:
                            res_data = await response.text()
                        
                        return {
                            "status": "success", 
                            "data": {
                                "result": res_data,
                                "headers": res_headers,
                                "status_code": status_code
                            }
                        }
                
                return {"status": "error", "error": f"Request failed or method not supported properly"}

        except Exception as e:
            return {"status": "error", "error": f"HTTP Request Failed: {str(e)}"}
