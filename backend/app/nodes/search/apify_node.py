"""
Apify Actor Node - Studio Standard
Batch 48: Browsing & Search
"""
from typing import Any, Dict, Optional, List
import json
from ...base import BaseNode
from ...registry import register_node

@register_node("apify_node")
class ApifyNode(BaseNode):
    """
    Run Apify Actors to extract data from websites, social media, and more.
    """
    node_type = "apify_node"
    version = "1.0.0"
    category = "search"
    credentials_required = ["apify_auth"]

    inputs = {
        "actor_id": {
            "type": "string",
            "required": True,
            "default": "apify/website-content-crawler",
            "description": "Full ID of the actor (e.g., apify/instagram-scraper)"
        },
        "run_input": {
            "type": "json",
            "required": True,
            "description": "JSON input for the actor"
        },
        "wait_for_finish": {
            "type": "boolean",
            "default": True,
            "description": "Wait for actor to complete before returning"
        }
    }

    outputs = {
        "result": {"type": "array"},
        "run_id": {"type": "string"},
        "dataset_id": {"type": "string"}
    }

    async def execute(self, input_data: Any, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        try:
            from apify_client import ApifyClient
        except ImportError:
            return {"status": "error", "error": "apify-client not installed. Run: pip install apify-client"}

        try:
            # 1. Resolve Auth
            creds = await self.get_credential("apify_auth")
            token = creds.get("token") or creds.get("api_token") if creds else self.get_config("api_token")
            
            if not token:
                return {"status": "error", "error": "Apify Token is required."}

            client = ApifyClient(token)
            actor_id = self.get_config("actor_id")
            
            # Prepare Input
            run_input = self.get_config("run_input", {})
            if isinstance(input_data, dict):
                run_input.update(input_data)
            elif isinstance(input_data, str) and input_data.startswith("{"):
                try:
                    run_input.update(json.loads(input_data))
                except:
                    pass
            elif isinstance(input_data, str) and input_data:
                # Basic heuristic: if it's a URL, put it in startUrls if possible
                if "startUrls" in run_input:
                    run_input["startUrls"] = [{"url": input_data}]
                else:
                    run_input["url"] = input_data

            # 2. Run Actor
            wait_secs = 60 if self.get_config("wait_for_finish", True) else 1
            run = client.actor(actor_id).call(run_input=run_input, wait_secs=wait_secs)
            
            if not run:
                return {"status": "error", "error": "Actor call failed or timed out."}

            dataset_id = run.get("defaultDatasetId")
            run_id = run.get("id")

            result_items = []
            if self.get_config("wait_for_finish", True):
                # Fetch dataset items
                items_list = client.dataset(dataset_id).list_items().items
                result_items = items_list

            return {
                "status": "success",
                "data": {
                    "result": result_items,
                    "run_id": run_id,
                    "dataset_id": dataset_id,
                    "count": len(result_items)
                }
            }

        except Exception as e:
            return {"status": "error", "error": f"Apify execution failed: {str(e)}"}
