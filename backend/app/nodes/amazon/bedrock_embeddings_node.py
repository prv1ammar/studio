"""
Amazon Bedrock Embeddings Node - Studio Standard
Batch 30: AI Provider Nodes
"""
from typing import Any, Dict, Optional, List
from ...base import BaseNode
from ...registry import register_node

@register_node("amazon_bedrock_embeddings")
class AmazonBedrockEmbeddingsNode(BaseNode):
    """
    Generate embeddings using Amazon Bedrock embedding models.
    Supports Titan and Cohere embedding models.
    """
    node_type = "amazon_bedrock_embeddings"
    version = "1.0.0"
    category = "ai_providers"
    credentials_required = ["aws_bedrock"]

    inputs = {
        "model_id": {
            "type": "dropdown",
            "default": "amazon.titan-embed-text-v1",
            "options": [
                "amazon.titan-embed-text-v1",
                "amazon.titan-embed-text-v2:0",
                "cohere.embed-english-v3",
                "cohere.embed-multilingual-v3"
            ],
            "description": "Bedrock embedding model to use"
        },
        "region_name": {
            "type": "dropdown",
            "default": "us-east-1",
            "options": ["us-east-1", "us-west-2", "eu-west-1", "ap-southeast-1"],
            "description": "AWS region"
        },
        "text": {
            "type": "string",
            "required": True,
            "description": "Text to generate embeddings for"
        },
        "normalize": {
            "type": "boolean",
            "default": True,
            "description": "Normalize embeddings to unit length"
        }
    }

    outputs = {
        "embeddings": {"type": "array"},
        "dimension": {"type": "number"},
        "model_used": {"type": "string"}
    }

    async def execute(self, input_data: Any, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        try:
            # Import dependencies
            try:
                from langchain_aws import BedrockEmbeddings
                import boto3
            except ImportError as e:
                missing = "langchain_aws" if "langchain_aws" in str(e) else "boto3"
                return {
                    "status": "error",
                    "error": f"{missing} not installed. Run: pip install {missing}"
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
            model_id = self.get_config("model_id", "amazon.titan-embed-text-v1")
            region = self.get_config("region_name", "us-east-1")
            normalize = self.get_config("normalize", True)

            # Get text from input
            text = input_data if isinstance(input_data, str) else self.get_config("text", "")
            
            if not text:
                return {"status": "error", "error": "Text is required"}

            # Create boto3 session
            session = boto3.Session(
                aws_access_key_id=aws_access_key,
                aws_secret_access_key=aws_secret_key,
                aws_session_token=creds.get("aws_session_token") if creds else None
            )

            # Create Bedrock client
            client_params = {"region_name": region}
            endpoint_url = self.get_config("endpoint_url")
            if endpoint_url:
                client_params["endpoint_url"] = endpoint_url

            boto3_client = session.client("bedrock-runtime", **client_params)

            # Initialize embeddings model
            embeddings_model = BedrockEmbeddings(
                client=boto3_client,
                model_id=model_id,
                region_name=region
            )

            # Generate embeddings
            if isinstance(text, list):
                # Multiple texts
                embeddings = embeddings_model.embed_documents(text)
            else:
                # Single text
                embedding = embeddings_model.embed_query(text)
                embeddings = [embedding]

            # Normalize if requested
            if normalize:
                import numpy as np
                embeddings = [
                    (np.array(emb) / np.linalg.norm(emb)).tolist()
                    for emb in embeddings
                ]

            # Get dimension
            dimension = len(embeddings[0]) if embeddings else 0

            return {
                "status": "success",
                "data": {
                    "embeddings": embeddings[0] if not isinstance(text, list) else embeddings,
                    "dimension": dimension,
                    "model_used": model_id
                }
            }

        except Exception as e:
            return {
                "status": "error",
                "error": f"Amazon Bedrock Embeddings error: {str(e)}"
            }
