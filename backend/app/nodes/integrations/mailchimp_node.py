from typing import Any, Dict, Optional
from pydantic import Field
from app.nodes.base import BaseNode, NodeConfig
from app.nodes.registry import register_node
try:
    from mailchimp3 import MailChimp
except ImportError:
    MailChimp = None

class MailchimpConfig(NodeConfig):
    api_key: Optional[str] = Field(None, description="Mailchimp API Key")
    username: Optional[str] = Field(None, description="Mailchimp Username")
    list_id: Optional[str] = Field(None, description="Target List/Audience ID")
    credentials_id: Optional[str] = Field(None, description="Mailchimp Credentials ID")

@register_node("mailchimp_node")
class MailchimpNode(BaseNode):
    node_id = "mailchimp_node"
    config_model = MailchimpConfig

    async def execute(self, input_data: Any, context: Optional[Dict[str, Any]] = None) -> Any:
        if not MailChimp:
            return {"error": "mailchimp3 library not installed."}

        # 1. Auth Retrieval
        creds = await self.get_credential("credentials_id")
        api_key = creds.get("api_key") if creds else self.get_config("api_key")
        username = creds.get("username") if creds else self.get_config("username")
        list_id = self.get_config("list_id")

        if not api_key or not username or not list_id:
            return {"error": "Mailchimp Username, API Key, and List ID are required."}

        try:
            client = MailChimp(mc_api=api_key, mc_user=username)
            
            # Simple Add Subscriber implementation
            email = None
            merge_fields = {}
            
            if isinstance(input_data, dict):
                email = input_data.get("email")
                merge_fields = input_data.get("merge_fields", {})
            else:
                email = str(input_data)

            if not email:
                return {"error": "No email address provided for subscription."}

            client.lists.members.create(list_id, {
                'email_address': email,
                'status': 'subscribed',
                'merge_fields': merge_fields
            })
            
            return {"status": "success", "email": email, "list_id": list_id}
            
        except Exception as e:
            return {"error": f"Mailchimp API Failure: {str(e)}"}
