"""
AWS S3 Node - Studio Standard (Universal Method)
Batch 94: Cloud Storage (n8n Critical)
"""
from typing import Any, Dict, Optional, List
import boto3
import json
from ...base import BaseNode
from ...registry import register_node

@register_node("aws_s3_node")
class AWSS3Node(BaseNode):
    """
    Manage objects in AWS S3 buckets.
    """
    node_type = "aws_s3_node"
    version = "1.0.0"
    category = "storage"
    credentials_required = ["aws_auth"]

    inputs = {
        "action": {
            "type": "dropdown",
            "default": "list_buckets",
            "options": ["list_buckets", "list_objects", "get_object", "put_object", "delete_object"],
            "description": "S3 action"
        },
        "bucket_name": {
            "type": "string",
            "optional": True
        },
        "key": {
            "type": "string",
            "optional": True
        },
        "body": {
            "type": "string",
            "optional": True,
            "description": "Content for PutObject"
        }
    }

    outputs = {
        "result": {"type": "any"},
        "status": {"type": "string"}
    }

    async def execute(self, input_data: Any, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        try:
            # 1. Authentication
            creds = await self.get_credential("aws_auth")
            access_key = creds.get("access_key")
            secret_key = creds.get("secret_key")
            region = creds.get("region", "us-east-1")
            
            if not access_key or not secret_key:
                return {"status": "error", "error": "AWS Access Key and Secret Key required."}

            # 2. Connect to Real API (boto3)
            # Note: boto3 is synchronous, should ideally run in executor for heavy operations
            session = boto3.Session(
                aws_access_key_id=access_key,
                aws_secret_access_key=secret_key,
                region_name=region
            )
            s3 = session.client('s3')
            
            action = self.get_config("action", "list_buckets")

            if action == "list_buckets":
                response = s3.list_buckets()
                buckets = [{"Name": b["Name"], "CreationDate": b["CreationDate"].isoformat()} for b in response.get("Buckets", [])]
                return {"status": "success", "data": {"result": buckets}}

            elif action == "list_objects":
                bucket = self.get_config("bucket_name")
                if not bucket:
                    return {"status": "error", "error": "bucket_name required"}
                    
                response = s3.list_objects_v2(Bucket=bucket)
                contents = response.get("Contents", [])
                objects = [{"Key": obj["Key"], "Size": obj["Size"], "LastModified": obj["LastModified"].isoformat()} for obj in contents]
                return {"status": "success", "data": {"result": objects}}

            elif action == "get_object":
                bucket = self.get_config("bucket_name")
                key = self.get_config("key") or str(input_data)
                
                if not bucket or not key:
                    return {"status": "error", "error": "bucket_name and key required"}
                    
                response = s3.get_object(Bucket=bucket, Key=key)
                body = response['Body'].read().decode('utf-8')
                return {"status": "success", "data": {"result": body}}

            elif action == "put_object":
                bucket = self.get_config("bucket_name")
                key = self.get_config("key")
                body = self.get_config("body") or str(input_data)
                
                if not bucket or not key:
                    return {"status": "error", "error": "bucket_name and key required"}
                
                s3.put_object(Bucket=bucket, Key=key, Body=body)
                return {"status": "success", "data": {"result": {"message": f"Successfully uploaded to {bucket}/{key}"}}}

            elif action == "delete_object":
                bucket = self.get_config("bucket_name")
                key = self.get_config("key")
                
                if not bucket or not key:
                    return {"status": "error", "error": "bucket_name and key required"}
                
                s3.delete_object(Bucket=bucket, Key=key)
                return {"status": "success", "data": {"result": {"message": f"Successfully deleted {bucket}/{key}"}}}

            return {"status": "error", "error": f"Unsupported action: {action}"}

        except Exception as e:
            return {"status": "error", "error": f"AWS S3 Node Failed: {str(e)}"}
