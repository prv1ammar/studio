"""
Webflow Node - Studio Standard
Batch 71: CMS & Web Engines
"""
from typing import Any, Dict, Optional, List
import aiohttp
from ...base import BaseNode
from ...registry import register_node

@register_node("webflow_node")
class WebflowNode(BaseNode):
    """
    Manage sites, collections, and items via the Webflow Data API v2.
    """
    node_type = "webflow_node"
    version = "1.0.0"
    category = "cms"
    credentials_required = ["webflow_auth"]

    inputs = {
        "action": {
            "type": "dropdown",
            "default": "list_sites",
            "options": ["list_sites", "list_collections", "list_items", "create_item"],
            "description": "Webflow action"
        },
        "site_id": {
            "type": "string",
            "optional": True,
            "description": "ID of the Webflow site"
        },
        "collection_id": {
            "type": "string",
            "optional": True,
            "description": "ID of the collection"
        },
        "item_data": {
            "type": "json",
            "optional": True,
            "description": "Fields for creating a CMS item"
        }
    }

    outputs = {
        "result": {"type": "any"},
        "status": {"type": "string"},
        "count": {"type": "number"}
    }

    async def execute(self, input_data: Any, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        try:
            creds = await self.get_credential("webflow_auth")
            access_token = creds.get("access_token") if creds else self.get_config("access_token")
            
            if not access_token:
                return {"status": "error", "error": "Webflow Access Token is required."}

            headers = {
                "Authorization": f"Bearer {access_token}",
                "Accept": "application/json",
                "Content-Type": "application/json"
            }
            
            base_url = "https://api.webflow.com/v2"
            action = self.get_config("action", "list_sites")

            async with aiohttp.ClientSession() as session:
                if action == "list_sites":
                    async with session.get(f"{base_url}/sites", headers=headers) as resp:
                        res_data = await resp.json()
                        sites = res_data.get("sites", [])
                        return {"status": "success", "data": {"result": sites, "count": len(sites)}}

                elif action == "list_collections":
                    site_id = self.get_config("site_id")
                    if not site_id:
                        return {"status": "error", "error": "site_id is required to list collections."}
                    async with session.get(f"{base_url}/sites/{site_id}/collections", headers=headers) as resp:
                        res_data = await resp.json()
                        collections = res_data.get("collections", [])
                        return {"status": "success", "data": {"result": collections, "count": len(collections)}}

                elif action == "list_items":
                    collection_id = self.get_config("collection_id")
                    if not collection_id:
                        return {"status": "error", "error": "collection_id is required to list items."}
                    async with session.get(f"{base_url}/collections/{collection_id}/items", headers=headers) as resp:
                        res_data = await resp.json()
                        items = res_data.get("items", [])
                        return {"status": "success", "data": {"result": items, "count": len(items)}}

                elif action == "create_item":
                    collection_id = self.get_config("collection_id")
                    if not collection_id:
                        return {"status": "error", "error": "collection_id is required to create an item."}
                    
                    fields = self.get_config("item_data") or input_data
                    if not isinstance(fields, dict):
                        fields = {"fieldData": fields} if isinstance(fields, str) else fields

                    payload = {"fieldData": fields} if "fieldData" not in fields else fields
                    
                    async with session.post(f"{base_url}/collections/{collection_id}/items", headers=headers, json=payload) as resp:
                        res_data = await resp.json()
                        return {"status": "success", "data": {"result": res_data, "status": "created"}}

                return {"status": "error", "error": f"Unsupported action: {action}"}

        except Exception as e:
            return {"status": "error", "error": f"Webflow Node Failed: {str(e)}"}
