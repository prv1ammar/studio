"""
Microsoft Excel Node - Studio Standard (Universal Method)
Batch 91: Productivity Suite (n8n Critical)
"""
from typing import Any, Dict, Optional, List
import aiohttp
from ...base import BaseNode
from ...registry import register_node

@register_node("excel_node")
class ExcelNode(BaseNode):
    """
    Manage Excel workbooks and worksheets via Microsoft Graph API.
    """
    node_type = "excel_node"
    version = "1.0.0"
    category = "productivity"
    credentials_required = ["microsoft_auth"]

    inputs = {
        "action": {
            "type": "dropdown",
            "default": "add_row",
            "options": ["add_row", "get_worksheet", "list_worksheets", "update_range"],
            "description": "Excel action"
        },
        "workbook_id": {
            "type": "string",
            "optional": True
        },
        "worksheet_name": {
            "type": "string",
            "default": "Sheet1",
            "optional": True
        },
        "values": {
            "type": "string",
            "optional": True,
            "description": "JSON array of values"
        }
    }

    outputs = {
        "result": {"type": "any"},
        "status": {"type": "string"}
    }

    async def execute(self, input_data: Any, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        try:
            # 1. Authentication
            creds = await self.get_credential("microsoft_auth")
            access_token = creds.get("access_token")
            
            if not access_token:
                return {"status": "error", "error": "Microsoft Access Token required."}

            headers = {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json"
            }
            
            # 2. Connect to Real API (Microsoft Graph)
            base_url = "https://graph.microsoft.com/v1.0"
            action = self.get_config("action", "add_row")
            workbook_id = self.get_config("workbook_id")

            if not workbook_id:
                return {"status": "error", "error": "workbook_id required"}

            async with aiohttp.ClientSession() as session:
                if action == "add_row":
                    worksheet = self.get_config("worksheet_name", "Sheet1")
                    values = self.get_config("values") or str(input_data)
                    
                    # Parse values if string
                    import json
                    if isinstance(values, str):
                        try:
                            values = json.loads(values)
                        except:
                            values = [values]
                    
                    url = f"{base_url}/me/drive/items/{workbook_id}/workbook/worksheets/{worksheet}/tables/Table1/rows"
                    payload = {
                        "values": [values] if not isinstance(values[0], list) else values
                    }
                    async with session.post(url, headers=headers, json=payload) as resp:
                        if resp.status not in [200, 201]:
                            return {"status": "error", "error": f"Excel API Error: {resp.status}"}
                        res_data = await resp.json()
                        return {"status": "success", "data": {"result": res_data}}

                elif action == "list_worksheets":
                    url = f"{base_url}/me/drive/items/{workbook_id}/workbook/worksheets"
                    async with session.get(url, headers=headers) as resp:
                        if resp.status != 200:
                            return {"status": "error", "error": f"Excel API Error: {resp.status}"}
                        res_data = await resp.json()
                        return {"status": "success", "data": {"result": res_data.get("value", [])}}

                return {"status": "error", "error": f"Unsupported action: {action}"}

        except Exception as e:
            return {"status": "error", "error": f"Excel Node Failed: {str(e)}"}
