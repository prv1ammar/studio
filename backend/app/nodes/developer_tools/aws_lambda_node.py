"""
AWS Lambda Node - Studio Standard (Universal Method)
Batch 110: Developer Tools & Databases
"""
from typing import Any, Dict, Optional
import aiohttp
from ..base import BaseNode
from ..registry import register_node

# Similar to S3/Wasabi, running AWS logic without boto3 is complex due to SigV4.
# Assuming boto3 or aiobotocore is available or using a simple API Gateway trigger URL if provided.
# Since AWS Lambda is often triggered directly via API Gateway in low-code, we'll support both "API Gateway URL" (simple) or "Direct Invoke" (placeholder for library).

@register_node("aws_lambda_node")
class AWSLambdaNode(BaseNode):
    """
    AWS Lambda generic invocation.
    """
    node_type = "aws_lambda_node"
    version = "1.0.0"
    category = "developer_tools"
    credentials_required = ["aws_lambda_auth"]


    properties = [
        {
            'displayName': 'Operation',
            'name': 'operation',
            'type': 'options',
            'default': 'invoke',
            'options': [
                {'name': 'Invoke', 'value': 'invoke'},
            ],
            'description': 'Lambda action',
        },
        {
            'displayName': 'Function Name',
            'name': 'function_name',
            'type': 'string',
            'default': '',
        },
        {
            'displayName': 'Payload',
            'name': 'payload',
            'type': 'string',
            'default': '',
            'description': 'JSON payload',
        },
    ]
    inputs = {
        "action": {
            "type": "dropdown",
            "default": "invoke",
            "options": ["invoke"],
            "description": "Lambda action"
        },
        "function_name": {
            "type": "string",
            "optional": True
        },
        "payload": {
            "type": "string",
            "optional": True,
            "description": "JSON payload"
        }
    }

    outputs = {
        "result": {"type": "any"},
        "status": {"type": "string"}
    }

    async def execute(self, input_data: Any, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        try:
            creds = await self.get_credential("aws_lambda_auth")
            access_key = creds.get("access_key")
            secret_key = creds.get("secret_key")
            region = creds.get("region", "us-east-1")
            
            # If using API gateway URL stored in creds, it's simpler
            api_gateway_url = creds.get("api_gateway_url")
            
            action = self.get_config("action", "invoke")

            async with aiohttp.ClientSession() as session:
                if action == "invoke":
                    payload_str = self.get_config("payload", "{}")
                    import json
                    try:
                        payload = json.loads(payload_str)
                    except:
                        return {"status": "error", "error": "Invalid JSON in payload"}
                    
                    if api_gateway_url:
                        # Simple POST to API Gateway
                        async with session.post(api_gateway_url, json=payload) as resp:
                            if resp.status != 200:
                                error_text = await resp.text()
                                return {"status": "error", "error": f"Lambda Error {resp.status}: {error_text}"}
                            
                            try:
                                res_data = await resp.json()
                            except:
                                res_data = await resp.text()
                            return {"status": "success", "data": {"result": res_data}}
                    else:
                        # Direct invocation requires Signature V4 signing or boto3
                        # Returning placeholder error
                        return {"status": "error", "error": "Direct AWS Lambda invocation requires 'aiobotocore' or 'boto3'. Please provide an API Gateway URL in credentials for HTTP invocation."}

            return {"status": "error", "error": f"Unsupported action: {action}"}

        except Exception as e:
            return {"status": "error", "error": f"AWS Lambda Node Failed: {str(e)}"}