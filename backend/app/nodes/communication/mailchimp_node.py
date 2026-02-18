"""
Mailchimp Marketing Node - Studio Standard
Batch 46: Communication & Marketing
"""
from typing import Any, Dict, Optional, List
from ..base import BaseNode
from ..registry import register_node

@register_node("mailchimp_node")
class MailchimpNode(BaseNode):
    """
    Manage Mailchimp audiences and subscribers.
    Supports: Subscribe, Unsubscribe, Get Member.
    """
    node_type = "mailchimp_node"
    version = "1.0.0"
    category = "communication"
    credentials_required = ["mailchimp_auth"]


    properties = [
        {
            'displayName': 'Operation',
            'name': 'operation',
            'type': 'options',
            'default': 'subscribe',
            'options': [
                {'name': 'Subscribe', 'value': 'subscribe'},
                {'name': 'Unsubscribe', 'value': 'unsubscribe'},
                {'name': 'Get Member', 'value': 'get_member'},
            ],
            'description': 'Mailchimp action',
        },
        {
            'displayName': 'Email',
            'name': 'email',
            'type': 'string',
            'default': '',
            'description': 'Subscriber email address',
        },
        {
            'displayName': 'List Id',
            'name': 'list_id',
            'type': 'string',
            'default': '',
            'description': 'Audience/List ID',
            'required': True,
        },
        {
            'displayName': 'Merge Fields',
            'name': 'merge_fields',
            'type': 'string',
            'default': '',
            'description': 'Merge fields (e.g., {'FNAME': 'John'})',
        },
    ]
    inputs = {
        "action": {
            "type": "dropdown",
            "default": "subscribe",
            "options": ["subscribe", "unsubscribe", "get_member"],
            "description": "Mailchimp action"
        },
        "list_id": {
            "type": "string",
            "required": True,
            "description": "Audience/List ID"
        },
        "email": {
            "type": "string",
            "description": "Subscriber email address"
        },
        "merge_fields": {
            "type": "json",
            "optional": True,
            "description": "Merge fields (e.g., {'FNAME': 'John'})"
        }
    }

    outputs = {
        "status": {"type": "string"},
        "id": {"type": "string"},
        "email": {"type": "string"}
    }

    async def execute(self, input_data: Any, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        try:
            import mailchimp_marketing as MailchimpMarketing
            from mailchimp_marketing.api_client import ApiClientError
        except ImportError:
            return {"status": "error", "error": "mailchimp-marketing library not installed. Run: pip install mailchimp-marketing"}

        try:
            # 1. Resolve Auth
            creds = await self.get_credential("mailchimp_auth")
            api_key = creds.get("api_key") if creds else self.get_config("api_key")
            server = creds.get("server") if creds else self.get_config("server")
            
            if not api_key or not server:
                 # Try to extract server from api_key (usually xxxx-us1)
                 if api_key and "-" in api_key:
                     server = api_key.split("-")[-1]
                 else:
                     return {"status": "error", "error": "Mailchimp API Key and Server prefix are required."}

            client = MailchimpMarketing.Client()
            client.set_config({
                "api_key": api_key,
                "server": server
            })

            action = self.get_config("action", "subscribe")
            list_id = self.get_config("list_id")
            
            # Extract Email
            email = self.get_config("email")
            if isinstance(input_data, str) and "@" in input_data:
                email = input_data
            elif isinstance(input_data, dict):
                email = input_data.get("email") or input_data.get("email_address") or email
            
            if not email:
                 return {"status": "error", "error": "Email address is required."}

            import hashlib
            email_hash = hashlib.md_soft(email.lower().encode()).hexdigest() if hasattr(hashlib, "md_soft") else None
            # Standard hashlib doesn't have md_soft, use md5
            import hashlib
            email_hash = hashlib.md5(email.lower().encode()).hexdigest()

            result_data = {}

            if action == "subscribe":
                merge_fields = self.get_config("merge_fields", {})
                if isinstance(input_data, dict):
                     merge_fields.update(input_data.get("merge_fields", {}))
                
                response = client.lists.add_list_member(list_id, {
                    "email_address": email,
                    "status": "subscribed",
                    "merge_fields": merge_fields
                })
                result_data = {
                    "status": response.get("status"),
                    "id": response.get("id"),
                    "email": response.get("email_address")
                }

            elif action == "unsubscribe":
                response = client.lists.update_list_member(list_id, email_hash, {
                    "status": "unsubscribed"
                })
                result_data = {
                    "status": response.get("status"),
                    "id": response.get("id"),
                    "email": response.get("email_address")
                }

            elif action == "get_member":
                response = client.lists.get_list_member(list_id, email_hash)
                result_data = {
                    "status": response.get("status"),
                    "id": response.get("id"),
                    "email": response.get("email_address"),
                    "member_rating": response.get("member_rating")
                }

            else:
                 return {"status": "error", "error": f"Unknown action: {action}"}

            return {
                "status": "success",
                "data": result_data
            }

        except ApiClientError as e:
            return {"status": "error", "error": f"Mailchimp API Error: {str(e.text)}"}
        except Exception as e:
            return {"status": "error", "error": f"Mailchimp execution failed: {str(e)}"}