from typing import Any, Dict, Optional, List
from ..base import BaseNode
from ..registry import register_node
import hubspot
from hubspot.crm.contacts import SimplePublicObjectInput, ApiException

@register_node("hubspot_crm")
class HubSpotNode(BaseNode):
    """
    Automate HubSpot CRM actions (Contacts, Search, etc.).
    """
    node_type = "hubspot_crm"
    version = "1.0.0"
    category = "integrations"
    credentials_required = ["hubspot_auth"]

    inputs = {
        "action": {"type": "string", "default": "create_contact", "enum": ["create_contact", "search_contact"]},
        "contact_data": {"type": "object", "optional": True, "description": "Properties for creation"}
    }
    outputs = {
        "id": {"type": "string"},
        "results": {"type": "array"},
        "status": {"type": "string"}
    }

    async def execute(self, input_data: Any, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        try:
            # 1. Resolve Auth
            creds = await self.get_credential("hubspot_auth")
            token = creds.get("access_token") if creds else self.get_config("access_token")
            
            if not token:
                return {"status": "error", "error": "HubSpot Access Token is required."}

            client = hubspot.Client.create(access_token=token)
            action = self.get_config("action", "create_contact")
            
            if action == "create_contact":
                properties = input_data if isinstance(input_data, dict) else self.get_config("contact_data", {})
                if not properties and isinstance(input_data, str):
                    properties = {"email": input_data}
                
                if not properties:
                    return {"status": "error", "error": "Properties dictionary is required for contact creation."}

                api_response = client.crm.contacts.basic_api.create(
                    simple_public_object_input=SimplePublicObjectInput(properties=properties)
                )
                res = api_response.to_dict()
                return {
                    "status": "success",
                    "data": {
                        "id": res.get("id"),
                        "properties": res.get("properties")
                    }
                }

            elif action == "search_contact":
                query = str(input_data) if input_data else self.get_config("contact_data", {}).get("email")
                if not query:
                    return {"status": "error", "error": "Search query (email) is required."}

                search_request = {
                    "filterGroups": [{"filters": [{"value": query, "propertyName": "email", "operator": "EQ"}]}]
                }
                api_response = client.crm.contacts.search_api.do_search(public_object_search_request=search_request)
                res = api_response.to_dict()
                return {
                    "status": "success",
                    "data": {
                        "results": res.get("results", []),
                        "total": res.get("total", 0)
                    }
                }

            return {"status": "error", "error": f"Unsupported action: {action}"}

        except ApiException as e:
             return {"status": "error", "error": f"HubSpot API Error: {e.reason}"}
        except Exception as e:
            return {"status": "error", "error": f"HubSpot Node Error: {str(e)}"}
