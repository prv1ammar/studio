import json
from typing import Any, Dict, Optional
from pydantic import Field
from app.nodes.base import BaseNode, NodeConfig
from app.nodes.registry import register_node
import aiohttp

class MailchimpConfig(NodeConfig):
    list_id: str = Field(..., description="Audience/List ID")
    credentials_id: Optional[str] = Field(None, description="Mailchimp API Key ID")

@register_node("mailchimp_add_member")
class MailchimpAddMemberNode(BaseNode):
    async def execute(self, input_data: Any, context: Optional[Dict[str, Any]] = None) -> Any:
        list_id = self.get_config("list_id")
        
        creds_data = await self.get_credential("credentials_id")
        api_key = creds_data.get("api_key") or creds_data.get("token") if creds_data else None
        
        if not api_key:
            return {"error": "Mailchimp API Key is required."}
            
        # Extract server prefix (e.g., from us1-us18)
        server = "us1"
        if "-" in api_key:
            server = api_key.split("-")[-1]
            
        email = input_data.get("email") if isinstance(input_data, dict) else str(input_data)
        if not "@" in email: 
            return {"error": f"Invalid email address: {email}"}
        
        url = f"https://{server}.api.mailchimp.com/3.0/lists/{list_id}/members"
        
        payload = {
            "email_address": email,
            "status": "subscribed",
            "merge_fields": input_data.get("fields", {}) if isinstance(input_data, dict) else {}
        }
        
        auth = aiohttp.BasicAuth("anyuser", api_key)

        async with aiohttp.ClientSession(auth=auth) as session:
            async with session.post(url, json=payload) as response:
                result = await response.json()
                if response.status >= 400:
                    return {"error": result.get("detail", "Mailchimp API Error"), "status": response.status}
                return {"id": result.get("id"), "status": result.get("status"), "email": email}
