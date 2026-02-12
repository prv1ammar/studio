import json
from typing import Any, Dict, Optional, List
from pydantic import Field
from app.nodes.base import BaseNode, NodeConfig
from app.nodes.registry import register_node
import gspread
from google.oauth2.service_account import Credentials

class GoogleSheetsConfig(NodeConfig):
    spreadsheet_id: str = Field(..., description="The ID of the Google Spreadsheet")
    sheet_name: str = Field("Sheet1", description="The name of the worksheet")
    credentials_id: Optional[str] = Field(None, description="Service Account Credentials ID")

@register_node("google_sheets_reader")
class GoogleSheetsReaderNode(BaseNode):
    async def execute(self, input_data: Any, context: Optional[Dict[str, Any]] = None) -> Any:
        spread_id = self.get_config("spreadsheet_id")
        sheet_name = self.get_config("sheet_name")
        
        creds_data = await self.get_credential("credentials_id")
        if not creds_data:
            return {"error": "Google Service Account credentials are required."}

        try:
            scope = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
            creds = Credentials.from_service_account_info(creds_data, scopes=scope)
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

@register_node("google_sheets_writer")
class GoogleSheetsWriterNode(BaseNode):
    async def execute(self, input_data: Any, context: Optional[Dict[str, Any]] = None) -> Any:
        spread_id = self.get_config("spreadsheet_id")
        sheet_name = self.get_config("sheet_name")
        
        creds_data = await self.get_credential("credentials_id")
        if not creds_data:
            return {"error": "Google Service Account credentials are required."}

        try:
            scope = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
            creds = Credentials.from_service_account_info(creds_data, scopes=scope)
            client = gspread.authorize(creds)
            
            sheet = client.open_by_key(spread_id).worksheet(sheet_name)
            
            if isinstance(input_data, list):
                if len(input_data) > 0 and isinstance(input_data[0], list):
                    sheet.append_rows(input_data)
                else:
                    sheet.append_row(input_data)
            elif isinstance(input_data, dict):
                # Try to append as row based on current headers if they exist
                headers = sheet.row_values(1)
                if headers:
                    row = [input_data.get(header, "") for header in headers]
                    sheet.append_row(row)
                else:
                    # No headers, just append values
                    sheet.append_row(list(input_data.values()))
            else:
                sheet.append_row([str(input_data)])
                
            return {"status": "success", "message": "Data written to Google Sheet"}
        except Exception as e:
            return {"error": f"Failed to write to Google Sheet: {str(e)}"}

@register_node("google_sheets_creator")
class GoogleSheetsCreatorNode(BaseNode):
    async def execute(self, input_data: Any, context: Optional[Dict[str, Any]] = None) -> Any:
        title = self.get_config("title") or (input_data if isinstance(input_data, str) else "New Spreadsheet")
        
        creds_data = await self.get_credential("credentials_id")
        if not creds_data:
            return {"error": "Google Service Account credentials are required."}

        try:
            scope = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
            creds = Credentials.from_service_account_info(creds_data, scopes=scope)
            client = gspread.authorize(creds)
            
            new_sheet = client.create(title)
            # By default, only the service account has access. 
            # We might want to share it with the user email if provided in config.
            share_email = self.get_config("share_with_email")
            if share_email:
                new_sheet.share(share_email, perm_type='user', role='writer')

            return {
                "status": "success", 
                "spreadsheet_id": new_sheet.id, 
                "url": f"https://docs.google.com/spreadsheets/d/{new_sheet.id}"
            }
        except Exception as e:
            return {"error": f"Failed to create Google Sheet: {str(e)}"}
