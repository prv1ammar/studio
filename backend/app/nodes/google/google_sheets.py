import gspread
from google.oauth2.service_account import Credentials
from typing import Any, Dict, Optional, List
from ..base import BaseNode
from ..registry import register_node

@register_node("google_sheets_action")
class GoogleSheetsNode(BaseNode):
    """
    Automate Google Sheets actions (Read, Write, Create).
    """
    node_type = "google_sheets_action"
    version = "1.0.0"
    category = "storage"
    credentials_required = ["google_service_account"]


    properties = [
        {
            'displayName': 'Operation',
            'name': 'operation',
            'type': 'string',
            'default': 'read_records',
        },
        {
            'displayName': 'Data',
            'name': 'data',
            'type': 'string',
            'default': '',
        },
        {
            'displayName': 'Sheet Name',
            'name': 'sheet_name',
            'type': 'string',
            'default': 'Sheet1',
        },
        {
            'displayName': 'Spreadsheet Id',
            'name': 'spreadsheet_id',
            'type': 'string',
            'default': '',
        },
    ]
    inputs = {
        "action": {"type": "string", "default": "read_records", "enum": ["read_records", "append_row", "create_spreadsheet"]},
        "spreadsheet_id": {"type": "string", "optional": True},
        "sheet_name": {"type": "string", "default": "Sheet1"},
        "data": {"type": "any", "optional": True}
    }
    outputs = {
        "results": {"type": "array"},
        "spreadsheet_id": {"type": "string"},
        "status": {"type": "string"}
    }

    async def execute(self, input_data: Any, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        try:
            # 1. Resolve Auth
            creds_info = await self.get_credential("google_service_account")
            if not creds_info:
                return {"status": "error", "error": "Google Service Account credentials are required."}

            scope = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
            creds = Credentials.from_service_account_info(creds_info, scopes=scope)
            client = gspread.authorize(creds)
            
            action = self.get_config("action", "read_records")

            if action == "create_spreadsheet":
                title = str(input_data) if isinstance(input_data, str) else self.get_config("data", "New Studio Sheet")
                sheet = client.create(title)
                return {
                    "status": "success",
                    "data": {
                        "spreadsheet_id": sheet.id,
                        "url": sheet.url
                    }
                }

            spread_id = self.get_config("spreadsheet_id")
            sheet_name = self.get_config("sheet_name", "Sheet1")
            if not spread_id:
                return {"status": "error", "error": "Spreadsheet ID is required for this action."}

            workbook = client.open_by_key(spread_id)
            worksheet = workbook.worksheet(sheet_name)

            if action == "read_records":
                data = worksheet.get_all_records()
                return {
                    "status": "success",
                    "data": {
                        "results": data,
                        "count": len(data)
                    }
                }

            elif action == "append_row":
                row_data = input_data if isinstance(input_data, list) else self.get_config("data")
                if isinstance(input_data, dict):
                    headers = worksheet.row_values(1)
                    if headers:
                        row_data = [input_data.get(h, "") for h in headers]
                    else:
                        row_data = list(input_data.values())
                
                if not row_data:
                    return {"status": "error", "error": "No data provided to append."}
                
                worksheet.append_row(row_data if isinstance(row_data, list) else [str(row_data)])
                return {"status": "success", "data": {"message": "Row appended successfully."}}

            return {"status": "error", "error": f"Unsupported action: {action}"}

        except Exception as e:
            return {"status": "error", "error": f"Google Sheets Node Error: {str(e)}"}