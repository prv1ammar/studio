"""
Expensify Node - Studio Standard (Universal Method)
Batch 85: SMB Finance
"""
from typing import Any, Dict, Optional, List
import aiohttp
import json
from ..base import BaseNode
from ..registry import register_node

@register_node("expensify_node")
class ExpensifyNode(BaseNode):
    """
    Automated expense reporting and receipt auditing via Expensify API.
    """
    node_type = "expensify_node"
    version = "1.0.0"
    category = "finance"
    credentials_required = ["expensify_auth"]


    properties = [
        {
            'displayName': 'Operation',
            'name': 'operation',
            'type': 'options',
            'default': 'get_reports',
            'options': [
                {'name': 'Get Reports', 'value': 'get_reports'},
                {'name': 'Create Expense', 'value': 'create_expense'},
                {'name': 'List Expenses', 'value': 'list_expenses'},
            ],
            'description': 'Expensify action',
        },
    ]
    inputs = {
        "action": {
            "type": "dropdown",
            "default": "get_reports",
            "options": ["get_reports", "create_expense", "list_expenses"],
            "description": "Expensify action"
        }
    }

    outputs = {
        "result": {"type": "any"},
        "status": {"type": "string"}
    }

    async def execute(self, input_data: Any, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        try:
            # 1. Authentication First
            creds = await self.get_credential("expensify_auth")
            partner_id = creds.get("partner_id") if creds else self.get_config("partner_id")
            partner_secret = creds.get("partner_secret") if creds else self.get_config("partner_secret")
            
            if not partner_id or not partner_secret:
                return {"status": "error", "error": "Expensify Partner ID and Secret are required."}

            # 2. Connect to Real API
            url = "https://integrations.expensify.com/Integration-Server/ExpensifyIntegrations"
            action = self.get_config("action", "get_reports")

            async with aiohttp.ClientSession() as session:
                if action == "get_reports":
                    # Expensify uses a specific 'requestJobDescription' JSON
                    job_desc = {
                        "type": "download",
                        "credentials": {
                            "partnerUserID": partner_id,
                            "partnerUserSecret": partner_secret
                        },
                        "onReceive": {
                            "immediateResponse": ["returnItemList"]
                        },
                        "inputSettings": {
                            "type": "reports",
                            "filters": {
                                "startDate": "2023-01-01"
                            }
                        }
                    }
                    
                    data = {
                        "requestJobDescription": json.dumps(job_desc)
                    }
                    
                    async with session.post(url, data=data) as resp:
                        if resp.status != 200:
                            return {"status": "error", "error": f"Expensify API Error: {resp.status}"}
                        res_data = await resp.json()
                        return {"status": "success", "data": {"result": res_data}}

                return {"status": "error", "error": f"Unsupported action: {action}"}

        except Exception as e:
            # 5. Error Handling
            return {"status": "error", "error": f"Expensify Node Failed: {str(e)}"}