from typing import Any, Dict, Optional, List
from pydantic import Field
from app.nodes.base import BaseNode, NodeConfig
from app.nodes.registry import register_node
import hubspot
from hubspot.crm.contacts import SimplePublicObjectInput, ApiException

class HubSpotConfig(NodeConfig):
    access_token: Optional[str] = Field(None, description="HubSpot Private App Access Token")
    credentials_id: Optional[str] = Field(None, description="HubSpot Credentials ID")
    action: str = Field("create_contact", description="HubSpot Action (create_contact, search_contact)")

@register_node("hubspot_node")
class HubSpotNode(BaseNode):
    node_id = "hubspot_node"
    config_model = HubSpotConfig

    async def execute(self, input_data: Any, context: Optional[Dict[str, Any]] = None) -> Any:
        # 1. Auth Retrieval
        creds = await self.get_credential("credentials_id")
        token = creds.get("token") if creds else self.get_config("access_token")
        
        if not token:
            return {"error": "HubSpot Access Token or Credentials ID are required."}

        # The hubspot-api-client is synchronous, but we can wrap it or just use it as is in our async execute
        # For better performance in a high-scale env, we'd use aiohttp directly.
        client = hubspot.Client.create(access_token=token)

        action = self.get_config("action")
        
        try:
            if action == "create_contact":
                # input_data should be a dict of properties
                properties = input_data if isinstance(input_data, dict) else {"email": str(input_data)}
                simple_public_object_input = SimplePublicObjectInput(properties=properties)
                api_response = client.crm.contacts.basic_api.create(simple_public_object_input=simple_public_object_input)
                return api_response.to_dict()
            
            elif action == "search_contact":
                # Search by email for simplicity
                query = str(input_data)
                search_request = {
                    "filterGroups": [
                        {
                            "filters": [
                                {
                                    "value": query,
                                    "propertyName": "email",
                                    "operator": "EQ"
                                }
                            ]
                        }
                    ]
                }
                api_response = client.crm.contacts.search_api.do_search(public_object_search_request=search_request)
                return api_response.to_dict()

            return {"error": f"Unsupported HubSpot action: {action}"}
            
        except ApiException as e:
            return {"error": f"HubSpot API Exception: {e.reason}", "message": e.body}
        except Exception as e:
            return {"error": f"Unexpected HubSpot Node Error: {str(e)}"}
