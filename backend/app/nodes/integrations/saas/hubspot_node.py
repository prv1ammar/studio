"""
HubSpot CRM Integration Node - Studio Standard
Batch 44: SaaS Integrations
"""
from typing import Any, Dict, Optional, List
from ...base import BaseNode
from ...registry import register_node

@register_node("hubspot_node")
class HubSpotNode(BaseNode):
    """
    Interact with HubSpot CRM.
    Supports: Create Contact, Get Deal, Search Contact, List Companies.
    """
    node_type = "hubspot_node"
    version = "1.0.0"
    category = "saas"
    credentials_required = ["hubspot_auth"]

    inputs = {
        "action": {
            "type": "dropdown",
            "default": "create_contact",
            "options": ["create_contact", "get_deal", "search_contact", "list_companies"],
            "description": "HubSpot action to perform"
        },
        "properties": {
            "type": "json",
            "description": "JSON object with HubSpot properties"
        },
        "target_id": {
            "type": "string",
            "optional": True,
            "description": "Specific ID (Deal ID, Record ID, etc.)"
        }
    }

    outputs = {
        "id": {"type": "string"},
        "item": {"type": "object"},
        "results": {"type": "array"}
    }

    async def execute(self, input_data: Any, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        try:
            import hubspot
            from hubspot.crm.contacts import SimplePublicObjectInput, ApiException
        except ImportError:
            return {"status": "error", "error": "hubspot-api-client not installed. Run: pip install hubspot-api-client"}

        try:
            # 1. Resolve Auth
            creds = await self.get_credential("hubspot_auth")
            token = None
            if creds:
                token = creds.get("access_token") or creds.get("api_key")
            
            if not token:
                token = self.get_config("access_token")

            if not token:
                return {"status": "error", "error": "HubSpot Access Token is required."}

            client = hubspot.Client.create(access_token=token)
            action = self.get_config("action", "create_contact")
            
            # Prepare Data
            props = self.get_config("properties", {})
            if isinstance(input_data, dict):
                props.update(input_data)
            elif isinstance(input_data, str) and input_data:
                 if action == "create_contact":
                     props["email"] = input_data
                 elif action == "search_contact":
                     props["email"] = input_data

            result_data = {}

            if action == "create_contact":
                if not props:
                     return {"status": "error", "error": "Properties are required to create a contact."}
                
                response = client.crm.contacts.basic_api.create(
                    simple_public_object_input=SimplePublicObjectInput(properties=props)
                )
                res_dict = response.to_dict()
                result_data = {
                    "id": res_dict.get("id"),
                    "item": res_dict
                }

            elif action == "search_contact":
                email = props.get("email")
                if not email:
                     return {"status": "error", "error": "Email property is required for contact search."}
                
                search_request = {
                    "filterGroups": [{"filters": [{"value": email, "propertyName": "email", "operator": "EQ"}]}]
                }
                response = client.crm.contacts.search_api.do_search(public_object_search_request=search_request)
                res_dict = response.to_dict()
                result_data = {
                    "results": res_dict.get("results", []),
                    "total": res_dict.get("total", 0)
                }

            elif action == "get_deal":
                deal_id = self.get_config("target_id") or (input_data if isinstance(input_data, str) else None)
                if not deal_id:
                     return {"status": "error", "error": "Deal ID is required (as target_id or input)."}
                
                response = client.crm.deals.basic_api.get_by_id(deal_id=deal_id)
                res_dict = response.to_dict()
                result_data = {
                    "id": res_dict.get("id"),
                    "item": res_dict
                }

            elif action == "list_companies":
                response = client.crm.companies.basic_api.get_page(limit=10)
                res_dict = response.to_dict()
                result_data = {
                    "results": res_dict.get("results", []),
                    "total": len(res_dict.get("results", []))
                }

            else:
                 return {"status": "error", "error": f"Unknown action: {action}"}

            return {
                "status": "success",
                "data": result_data
            }

        except ApiException as e:
             return {"status": "error", "error": f"HubSpot API Error: {str(e)}"}
        except Exception as e:
            return {"status": "error", "error": f"HubSpot execution failed: {str(e)}"}
