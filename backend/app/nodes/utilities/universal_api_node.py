from ..base import BaseNode
from ..registry import register_node
from typing import Any, Dict, Optional
import json

@register_node("universal_api_node")
class UniversalAPIConnectorNode(BaseNode):
    """
    Standardized Node for interacting with any REST API.
    Replaces multiple hardcoded 'ghost' nodes.
    """
    node_type = "http_request"
    version = "1.0.0"
    category = "integrations"

    properties = [
        {
            'displayName': 'Body',
            'name': 'body',
            'type': 'string',
            'default': '',
            'description': 'Request body (for POST/PUT)',
        },
        {
            'displayName': 'Headers',
            'name': 'headers',
            'type': 'string',
            'default': {},
        },
        {
            'displayName': 'Method',
            'name': 'method',
            'type': 'string',
            'default': 'GET',
        },
        {
            'displayName': 'Params',
            'name': 'params',
            'type': 'string',
            'default': '',
            'description': 'Query parameters',
        },
        {
            'displayName': 'Url',
            'name': 'url',
            'type': 'string',
            'default': '',
            'description': 'Target URL',
        },
    ]
    inputs = {
        "url": {"type": "string", "description": "Target URL"},
        "method": {"type": "string", "default": "GET", "enum": ["GET", "POST", "PUT", "DELETE", "PATCH"]},
        "headers": {"type": "object", "default": {}},
        "body": {"type": "any", "description": "Request body (for POST/PUT)"},
        "params": {"type": "object", "description": "Query parameters"}
    }
    outputs = {
        "status": {"type": "string"},
        "data": {"type": "any", "description": "Response body"},
        "code": {"type": "number", "description": "HTTP Status Code"}
    }
    credentials_required = [] # varying based on usage
    
    async def execute(self, input_data: Any, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        try:
            import aiohttp
            import asyncio
        except ImportError:
            return {"status": "error", "error": "Error: 'aiohttp' package is required. Please run: pip install aiohttp"}

        try:
            # Flexible config retrieval
            base_url = self.get_config("api_url") or self.get_config("base_url") or self.get_config("url")
            api_key = self.get_config("api_key") or self.get_config("access_token")
            endpoint = self.get_config("endpoint", "")
            method = self.get_config("method", "GET").upper()
            action = self.get_config("action")
            
            # Using input_data as body/params if not explicitly configured
            payload = input_data
            
            if not base_url and isinstance(input_data, str) and input_data.startswith("http"):
                 base_url = input_data
                 payload = {} # Input absorbed as URL
            
            if not base_url:
                return {"status": "error", "error": "Error: API URL is required."}
            
            # Construct final URL
            if endpoint:
                url = f"{base_url.rstrip('/')}/{endpoint.lstrip('/')}"
            else:
                url = base_url
            
            # Prepare Headers
            headers = self.get_config("headers", {})
            if isinstance(headers, str):
                try: headers = json.loads(headers)
                except: headers = {}
                
            if "Content-Type" not in headers:
                headers["Content-Type"] = "application/json"
                
            if api_key:
                auth_type = self.get_config("auth_type")
                if auth_type == "Bearer":
                    headers["Authorization"] = f"Bearer {api_key}"
                elif auth_type == "xc-token":
                    headers["xc-token"] = api_key
                else:
                    headers["Authorization"] = f"Bearer {api_key}"

            # Prepare Payload
            if isinstance(payload, str) and method in ["POST", "PUT", "PATCH"]:
                 try: payload = json.loads(payload)
                 except: pass # Keep as string if not JSON

            if action and isinstance(payload, dict):
                payload["action"] = action
                
            print(f"Universal API (Async): {method} {url}")
            
            # Execute
            timeout = aiohttp.ClientTimeout(total=30)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                request_kwargs = {"headers": headers}
                
                if method in ["GET", "DELETE"]:
                    if isinstance(payload, dict):
                        request_kwargs["params"] = payload
                else:
                    request_kwargs["json"] = payload
                
                async with session.request(method, url, **request_kwargs) as resp:
                    status_code = resp.status
                    text_result = await resp.text()
                    
                    try:
                        data = await resp.json()
                    except:
                        data = text_result
                        
                    if status_code >= 400:
                        return {
                            "status": "error", 
                            "error": f"API Error ({status_code}): {text_result}", 
                            "code": status_code,
                            "data": data
                        }
                    
                    return {
                        "status": "success", 
                        "data": data, 
                        "code": status_code
                    }

        except Exception as e:
            return {"status": "error", "error": f"Universal API Execution Failed: {str(e)}"}

    async def get_langchain_object(self, context: Optional[Dict[str, Any]] = None) -> Any:
        try:
            from langchain.tools import Tool
            
            node_id = self.config.get("id", "universal_api_tool")
            description = self.config.get("description") or f"Execute API call for {node_id}. Input should be a query string or JSON dict."
            
            return Tool(
                name=node_id,
                description=description,
                func=lambda x: "Error: Use async version (execut_node) for real execution. This is a shim for Agent definition." if not context else None,
                coroutine=lambda x: self.execute(x, context)
            )
        except Exception as e:
            print(f"Error creating LangChain Tool for {self.__class__.__name__}: {e}")
            return None

# Register common IDs that should use the Universal API Connector
from ..registry import NodeRegistry

NodeRegistry.bulk_register([
    "sageNode", "odooNode", "dolibarrNode",
    "salesforceNode", "hubspotNode", "zohoNode", "sugarcrmNode", "vtigerNode",
    "zapierNode", "githubNode", "gitlabNode",
    "trelloNode", "glpiNode", "btrixNode", "unicaNode"
], UniversalAPIConnectorNode)