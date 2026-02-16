"""
API Request Tool Node - Studio Standard
Batch 37: Tools & Utilities
"""
import json
import httpx
from typing import Any, Dict, Optional, List
from ...base import BaseNode
from ...registry import register_node

@register_node("api_tool")
class APIToolNode(BaseNode):
    """
    Make robust HTTP requests with support for all methods, headers, and body.
    Features: GET/POST/PUT/DELETE, custom headers, query params, and JSON/form data.
    """
    node_type = "api_tool"
    version = "1.0.0"
    category = "tools"
    credentials_required = ["api_credential"]

    inputs = {
        "url": {
            "type": "string",
            "required": True,
            "description": "Full URL for the request"
        },
        "method": {
            "type": "dropdown",
            "default": "GET",
            "options": ["GET", "POST", "PUT", "DELETE", "PATCH"],
            "description": "HTTP method to use"
        },
        "headers": {
            "type": "json",
            "optional": True,
            "description": "Headers dictionary"
        },
        "auth_type": {
            "type": "dropdown",
            "default": "none",
            "options": ["none", "bearer", "basic", "header", "query"],
            "description": "How to apply credentials"
        },
        "auth_header_name": {
            "type": "string",
            "default": "Authorization",
            "description": "Custom header name for 'header' auth type"
        },
        "body": {
            "type": "json",
            "optional": True,
            "description": "Request body JSON or dictionary"
        },
        "query_params": {
            "type": "json",
            "optional": True,
            "description": "Query parameters dictionary"
        },
        "timeout": {
            "type": "number",
            "default": 30,
            "description": "Request timeout in seconds"
        }
    }

    outputs = {
        "status_code": {"type": "number"},
        "response": {"type": "json"},
        "headers": {"type": "json"},
        "success": {"type": "boolean"}
    }

    async def execute(self, input_data: Any, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        try:
            # Get URL
            url = input_data if isinstance(input_data, str) else self.get_config("url")
            
            if not url:
                return {"status": "error", "error": "URL is required"}

            # Get configuration
            method = self.get_config("method", "GET").upper()
            timeout = int(self.get_config("timeout", 30))
            
            headers = self.get_config("headers", {})
            if isinstance(headers, str):
                try:
                    headers = json.loads(headers)
                except:
                    return {"status": "error", "error": "Headers must be a valid JSON object"}

            params = self.get_config("query_params", {})
            if isinstance(params, str):
                try:
                    params = json.loads(params)
                except:
                    return {"status": "error", "error": "Query params must be a valid JSON object"}

            # Apply Credentials
            creds = await self.get_credential("api_credential")
            auth_type = self.get_config("auth_type", "none").lower()
            
            if creds and auth_type != "none":
                token = creds.get("token") or creds.get("api_key") or creds.get("access_token")
                
                if auth_type == "bearer":
                    headers["Authorization"] = f"Bearer {token}"
                elif auth_type == "basic":
                    import base64
                    user = creds.get("username", "")
                    pwd = creds.get("password", token)
                    auth_str = base64.b64encode(f"{user}:{pwd}".encode()).decode()
                    headers["Authorization"] = f"Basic {auth_str}"
                elif auth_type == "header":
                    header_name = self.get_config("auth_header_name", "Authorization")
                    headers[header_name] = token
                elif auth_type == "query":
                    param_name = self.get_config("auth_header_name", "api_key")
                    params[param_name] = token

            body = self.get_config("body", {})
            if isinstance(body, str):
                try:
                    body = json.loads(body)
                except:
                    pass

            # Prepare request
            async with httpx.AsyncClient(timeout=timeout) as client:
                request_kwargs = {
                    "method": method,
                    "url": url,
                    "headers": headers,
                    "params": params,
                    "follow_redirects": True
                }

                # Attach body based on type
                if method in ["POST", "PUT", "PATCH"]:
                    if isinstance(body, (dict, list)):
                        request_kwargs["json"] = body
                    else:
                        request_kwargs["content"] = str(body).encode("utf-8")

                # Perform request
                response = await client.request(**request_kwargs)
                
                # Parse response
                try:
                    response_json = response.json()
                except Exception:
                    response_json = {"text": response.text}

                return {
                    "status": "success",
                    "data": {
                        "status_code": response.status_code,
                        "response": response_json,
                        "headers": dict(response.headers),
                        "success": response.is_success,
                        "url": str(response.url)
                    }
                }

        except httpx.TimeoutException:
            return {"status": "error", "error": f"Request to {url} timed out after {timeout}s"}
        except httpx.RequestError as e:
            return {"status": "error", "error": f"Request failed: {str(e)}"}
        except Exception as e:
            return {"status": "error", "error": f"API Tool Execution Error: {str(e)}"}

