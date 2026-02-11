import json
from typing import Any, Dict, Optional, List
from pydantic import Field
from app.nodes.base import BaseNode, NodeConfig
from app.core.credentials import cred_manager
import gspread
from oauth2client.service_account import ServiceAccountCredentials

class GoogleSheetsConfig(NodeConfig):
    spreadsheet_id: str = Field(..., description="The ID of the Google Spreadsheet")
    sheet_name: str = Field("Sheet1", description="The name of the worksheet")
    credentials_id: Optional[str] = Field(None, description="Service Account Credentials ID")

class GoogleSheetsReaderNode(BaseNode):
    node_id = "google_sheets_reader"
    config_model = GoogleSheetsConfig

    async def execute(self, input_data: Any, context: Optional[Dict[str, Any]] = None) -> Any:
        spread_id = self.get_config("spreadsheet_id")
        sheet_name = self.get_config("sheet_name")
        
        # Get credentials
        creds_data = await self.get_credential("credentials_id")
        if not creds_data:
            return {"error": "Google Service Account credentials are required."}

        try:
            scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
            creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_data, scope)
            client = gspread.authorize(creds)
            
            sheet = client.open_by_key(spread_id).worksheet(sheet_name)
            
            # If input_data is a range (e.g. "A1:C10"), use it. Otherwise get all.
            if isinstance(input_data, str) and ":" in input_data:
                data = sheet.get(input_data)
            else:
                data = sheet.get_all_records()
                
            return data
        except Exception as e:
            return {"error": f"Failed to read Google Sheet: {str(e)}"}

class GoogleSheetsWriterNode(BaseNode):
    node_id = "google_sheets_writer"
    config_model = GoogleSheetsConfig

    async def execute(self, input_data: Any, context: Optional[Dict[str, Any]] = None) -> Any:
        spread_id = self.get_config("spreadsheet_id")
        sheet_name = self.get_config("sheet_name")
        
        creds_data = await self.get_credential("credentials_id")
        if not creds_data:
            return {"error": "Google Service Account credentials are required."}

        try:
            scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
            creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_data, scope)
            client = gspread.authorize(creds)
            
            sheet = client.open_by_key(spread_id).worksheet(sheet_name)
            
            if isinstance(input_data, list):
                if isinstance(input_data[0], list):
                    # Batch append
                    sheet.append_rows(input_data)
                else:
                    # Single row append
                    sheet.append_row(input_data)
            elif isinstance(input_data, dict):
                # Append dict by matching headers
                sheet.append_row(list(input_data.values()))
            else:
                # Fallback to simple string append
                sheet.append_row([str(input_data)])
                
            return {"status": "success", "message": "Data written to Google Sheet"}
        except Exception as e:
            return {"error": f"Failed to write to Google Sheet: {str(e)}"}

# Registration helper
from app.nodes.registry import register_node
register_node("google_sheets_reader")(GoogleSheetsReaderNode)
register_node("google_sheets_writer")(GoogleSheetsWriterNode)
