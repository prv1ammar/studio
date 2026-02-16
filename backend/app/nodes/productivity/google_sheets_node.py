"""
Google Sheets Integration Node - Studio Standard
Part of Phase 6: Rewriting Existing Nodes to remove Composio
"""
import json
import httpx
from typing import Any, Dict, Optional, List
from ...base import BaseNode
from ...registry import register_node

@register_node("google_sheets_node")
class GoogleSheetsNode(BaseNode):
    """
    Interact with Google Sheets directly via Google Sheets API.
    Supports: Get Spreadsheet, Append Row, Update Range, Clear Range, Get Values.
    Replaces Composio Google Sheets implementation.
    """
    node_type = "google_sheets_node"
    version = "1.0.0"
    category = "productivity"
    credentials_required = ["google_sheets_auth"]

    inputs = {
        "action": {
            "type": "dropdown",
            "default": "append_row",
            "options": [
                "get_spreadsheet",
                "append_row",
                "update_range",
                "clear_range",
                "get_values"
            ],
            "description": "Action to perform"
        },
        "spreadsheet_id": {
            "type": "string",
            "required": True,
            "description": "Google Spreadsheet ID"
        },
        "range": {
            "type": "string",
            "default": "Sheet1!A1",
            "description": "Range (e.g., Sheet1!A1:B10)"
        },
        "values": {
            "type": "json",
            "optional": True,
            "description": "Array of arrays for values (e.g., [[val1, val2]])"
        }
    }

    outputs = {
        "result": {"type": "json"},
        "spreadsheet_id": {"type": "string"},
        "updated_range": {"type": "string"},
        "status": {"type": "string"}
    }

    async def execute(self, input_data: Any, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        try:
            # 1. Get Credentials
            creds = await self.get_credential("google_sheets_auth")
            access_token = creds.get("access_token") if creds else None
            
            if not access_token:
                 return {"status": "error", "error": "Google Sheets access token required. Connect 'google_sheets_auth' in settings."}

            # 2. Setup Client
            headers = {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json"
            }
            
            base_url = "https://sheets.googleapis.com/v4/spreadsheets"
            action = self.get_config("action", "append_row")
            spreadsheet_id = self.get_config("spreadsheet_id")
            
            if not spreadsheet_id:
                 return {"status": "error", "error": "Spreadsheet ID is required."}

            async with httpx.AsyncClient(headers=headers, timeout=30.0) as client:
                
                result_data = {}
                
                if action == "get_spreadsheet":
                    resp = await client.get(f"{base_url}/{spreadsheet_id}")
                    resp.raise_for_status()
                    result_data = resp.json()

                elif action == "get_values":
                    target_range = self.get_config("range", "Sheet1")
                    resp = await client.get(f"{base_url}/{spreadsheet_id}/values/{target_range}")
                    resp.raise_for_status()
                    result_data = resp.json()

                elif action == "append_row":
                    target_range = self.get_config("range", "Sheet1")
                    values = self.get_config("values")
                    
                    if not values and input_data:
                        if isinstance(input_data, list):
                            if len(input_data) > 0 and isinstance(input_data[0], list):
                                values = input_data
                            else:
                                values = [input_data]
                        else:
                            values = [[str(input_data)]]
                    
                    if not values:
                        return {"status": "error", "error": "Values (array of arrays) are required for append_row."}
                        
                    url = f"{base_url}/{spreadsheet_id}/values/{target_range}:append?valueInputOption=USER_ENTERED"
                    payload = {"values": values}
                    resp = await client.post(url, json=payload)
                    resp.raise_for_status()
                    result_data = resp.json()

                elif action == "update_range":
                    target_range = self.get_config("range")
                    values = self.get_config("values") or input_data
                    
                    if not target_range or not values:
                        return {"status": "error", "error": "Range and values are required for update_range."}
                    
                    if not isinstance(values, list):
                        values = [[str(values)]]
                    elif len(values) > 0 and not isinstance(values[0], list):
                        values = [values]
                        
                    url = f"{base_url}/{spreadsheet_id}/values/{target_range}?valueInputOption=USER_ENTERED"
                    payload = {"values": values}
                    resp = await client.put(url, json=payload)
                    resp.raise_for_status()
                    result_data = resp.json()

                elif action == "clear_range":
                    target_range = self.get_config("range")
                    if not target_range:
                        return {"status": "error", "error": "Range is required for clear_range."}
                        
                    url = f"{base_url}/{spreadsheet_id}/values/{target_range}:clear"
                    resp = await client.post(url)
                    resp.raise_for_status()
                    result_data = resp.json()
                
                else:
                    return {"status": "error", "error": f"Unknown action: {action}"}

                return {
                    "status": "success",
                    "data": {
                        "result": result_data,
                        "spreadsheet_id": spreadsheet_id,
                        "updated_range": result_data.get("updatedRange"),
                        "status": "completed"
                    }
                }

        except httpx.HTTPStatusError as e:
            return {"status": "error", "error": f"Google Sheets API Error ({e.response.status_code}): {e.response.text}"}
        except Exception as e:
            return {"status": "error", "error": f"Google Sheets Node execution failed: {str(e)}"}
