"""
Amazon Bedrock Converse Node - Studio Standard
Batch 30: AI Provider Nodes
"""
from typing import Any, Dict, Optional
from ...base import BaseNode
from ...registry import register_node

@register_node("amazon_bedrock_converse")
class AmazonBedrockConverseNode(BaseNode):
    """
    Generate text using Amazon Bedrock LLMs with the modern Converse API.
    Supports Claude, Titan, and other Bedrock models.
    """
    node_type = "amazon_bedrock_converse"
    version = "1.0.0"
    category = "ai_providers"
    credentials_required = ["aws_bedrock"]

    inputs = {
        "model_id": {
            "type": "dropdown",
            "default": "anthropic.claude-3-5-sonnet-20241022-v2:0",
            "options": [
                "anthropic.claude-3-5-sonnet-20241022-v2:0",
                "anthropic.claude-3-haiku-20240307-v1:0",
                "anthropic.claude-3-opus-20240229-v1:0",
                "amazon.titan-text-express-v1",
                "amazon.titan-text-lite-v1",
                "meta.llama3-70b-instruct-v1:0",
                "mistral.mistral-7b-instruct-v0:2"
            ],
            "description": "Bedrock model to use"
        },
        "region_name": {
            "type": "dropdown",
            "default": "us-east-1",
            "options": ["us-east-1", "us-west-2", "eu-west-1", "ap-southeast-1"],
            "description": "AWS region"
        },
        "prompt": {
            "type": "string",
            "required": True,
            "description": "Input prompt for the model"
        },
        "temperature": {
            "type": "number",
            "default": 0.7,
            "min": 0,
            "max": 1,
            "description": "Controls randomness (0=deterministic, 1=creative)"
        },
        "max_tokens": {
            "type": "number",
            "default": 4096,
            "description": "Maximum tokens to generate"
        },
        "top_p": {
            "type": "number",
            "default": 0.9,
            "min": 0,
            "max": 1,
            "description": "Nucleus sampling parameter"
        },
        "disable_streaming": {
            "type": "boolean",
            "default": False,
            "description": "Disable streaming responses"
        }
    }

    outputs = {
        "response": {"type": "string"},
        "model_used": {"type": "string"},
        "tokens_used": {"type": "number"}
    }

    async def execute(self, input_data: Any, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        try:
            # Import here to avoid dependency issues
            try:
                from langchain_aws.chat_models.bedrock_converse import ChatBedrockConverse
            except ImportError:
                return {
                    "status": "error",
                    "error": "langchain_aws not installed. Run: pip install langchain_aws"
                }

            # Get credentials
            creds = await self.get_credential("aws_bedrock")
            aws_access_key = creds.get("aws_access_key_id") if creds else self.get_config("aws_access_key_id")
            aws_secret_key = creds.get("aws_secret_access_key") if creds else self.get_config("aws_secret_access_key")

            if not aws_access_key or not aws_secret_key:
                return {
                    "status": "error",
                    "error": "AWS credentials required (aws_access_key_id, aws_secret_access_key)"
                }

            # Get configuration
            model_id = self.get_config("model_id", "anthropic.claude-3-5-sonnet-20241022-v2:0")
            region = self.get_config("region_name", "us-east-1")
            temperature = self.get_config("temperature", 0.7)
            max_tokens = self.get_config("max_tokens", 4096)
            top_p = self.get_config("top_p", 0.9)
            disable_streaming = self.get_config("disable_streaming", False)

            # Get prompt from input
            prompt = input_data if isinstance(input_data, str) else self.get_config("prompt", "")
            
            if not prompt:
                return {"status": "error", "error": "Prompt is required"}

            # Initialize Bedrock client
            init_params = {
                "model": model_id,
                "region_name": region,
                "aws_access_key_id": aws_access_key,
                "aws_secret_access_key": aws_secret_key,
                "temperature": temperature,
                "max_tokens": max_tokens,
                "top_p": top_p,
                "disable_streaming": disable_streaming
            }

            # Add session token if available
            session_token = creds.get("aws_session_token") if creds else None
            if session_token:
                init_params["aws_session_token"] = session_token

            # Create model instance
            model = ChatBedrockConverse(**init_params)

            # Generate response
            if disable_streaming:
                response = model.invoke(prompt)
                response_text = response.content
            else:
                # For streaming, collect all chunks
                chunks = []
                for chunk in model.stream(prompt):
                    chunks.append(chunk.content)
                response_text = "".join(chunks)

            return {
                "status": "success",
                "data": {
                    "response": response_text,
                    "model_used": model_id,
                    "tokens_used": max_tokens  # Approximate, actual usage may vary
                }
            }

        except Exception as e:
            return {
                "status": "error",
                "error": f"Amazon Bedrock error: {str(e)}"
            }
