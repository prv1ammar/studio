from typing import Any, Dict, Optional, List
from ..base import BaseNode
from ..registry import register_node

@register_node("mailchimp_action")
class MailchimpNode(BaseNode):
    """
    Automate Mailchimp audience actions (Subscribe).
    """
    node_type = "mailchimp_action"
    version = "1.0.0"
    category = "communication"
    credentials_required = ["mailchimp_auth"]

    inputs = {
        "list_id": {"type": "string", "description": "Audience/List ID"},
        "email_address": {"type": "string", "optional": True}
    }
    outputs = {
        "status": {"type": "string"},
        "email": {"type": "string"}
    }

    async def execute(self, input_data: Any, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        try:
            from mailchimp3 import MailChimp
        except ImportError:
            return {"status": "error", "error": "Please install 'mailchimp3'."}

        try:
            # 1. Resolve Auth
            creds = await self.get_credential("mailchimp_auth")
            api_key = creds.get("api_key") if creds else self.get_config("api_key")
            username = creds.get("username") if creds else self.get_config("username")
            list_id = self.get_config("list_id")

            if not api_key or not list_id:
                 return {"status": "error", "error": "Mailchimp API Key and List ID are required."}

            client = MailChimp(mc_api=api_key, mc_user=username or "studio_user")
            
            # 2. Extract Data
            email = None
            merge_fields = {}
            if isinstance(input_data, dict):
                email = input_data.get("email") or input_data.get("email_address")
                merge_fields = input_data.get("merge_fields", {})
            else:
                email = str(input_data) if input_data else self.get_config("email_address")

            if not email:
                return {"status": "error", "error": "Email address is required."}

            client.lists.members.create(list_id, {
                'email_address': email,
                'status': 'subscribed',
                'merge_fields': merge_fields
            })
            
            return {
                "status": "success",
                "data": {
                    "email": email,
                    "list_id": list_id
                }
            }

        except Exception as e:
            return {"status": "error", "error": f"Mailchimp Node Error: {str(e)}"}
