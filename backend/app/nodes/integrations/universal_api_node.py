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
    
    async def execute(self, input_data: Any, context: Optional[Dict[str, Any]] = None) -> Any:
        try:
            import aiohttp
            import asyncio
        except ImportError:
            return "Error: 'aiohttp' package is required. Please run: pip install aiohttp"

        try:
            base_url = self.get_config("api_url") or self.get_config("base_url")
            api_key = self.get_config("api_key") or self.get_config("access_token")
            endpoint = self.get_config("endpoint", "")
            method = self.get_config("method", "GET").upper()
            action = self.get_config("action")
            
            if not base_url:
                return "Error: API URL is required."
            
            # Construct final URL
            if endpoint:
                url = f"{base_url.rstrip('/')}/{endpoint.lstrip('/')}"
            else:
                url = base_url
            
            # Prepare Headers
            headers = {
                "Content-Type": "application/json"
            }
            if api_key:
                # Common auth patterns
                if self.config.get("auth_type") == "Bearer":
                    headers["Authorization"] = f"Bearer {api_key}"
                elif self.config.get("auth_type") == "xc-token":
                    headers["xc-token"] = api_key
                else:
                    # Generic default
                    headers["Authorization"] = f"Bearer {api_key}"

            # Prepare Payload
            payload = input_data if isinstance(input_data, dict) else {"query": input_data}
            if action:
                payload["action"] = action

            print(f"Universal API (Async): {method} {url}")
            
            timeout = aiohttp.ClientTimeout(total=30)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                # Use generic request method for cleaner logic
                # For GET/DELETE, use params. For POST/PATCH/PUT, use json body.
                # Note: DELETE can technically have a body but usually doesn't in REST.
                request_kwargs = {
                    "headers": headers
                }
                
                if method in ["GET", "DELETE"]:
                    request_kwargs["params"] = payload
                else:
                    request_kwargs["json"] = payload
                
                async with session.request(method, url, **request_kwargs) as resp:
                    status = resp.status
                    text_result = await resp.text()
                    
                    if status >= 400:
                        return f"API Error ({status}): {text_result}"
                    
                    try:
                        return await resp.json()
                    except:
                        return text_result

        except Exception as e:
            return f"Universal API Execution Failed: {str(e)}"

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
