"""
Microsoft Productivity Nodes - Studio Standard (Universal Method)
Batch 105: Productivity Suite
"""
from typing import Any, Dict, Optional, List
import aiohttp
from ...base import BaseNode
from ...registry import register_node

# ============================================
# MICROSOFT OUTLOOK NODE
# ============================================
@register_node("microsoft_outlook_node")
class MicrosoftOutlookNode(BaseNode):
    """
    Microsoft Outlook integration via Graph API.
    """
    node_type = "microsoft_outlook_node"
    version = "1.0.0"
    category = "productivity"
    credentials_required = ["microsoft_graph_auth"]

    inputs = {
        "action": {
            "type": "dropdown",
            "default": "send_email",
            "options": ["send_email", "create_event", "list_events", "list_messages", "list_contacts"],
            "description": "Outlook action"
        },
        "to_recipients": {
            "type": "string",
            "optional": True,
            "description": "Comma separated emails"
        },
        "subject": {
            "type": "string",
            "optional": True
        },
        "content": {
            "type": "string",
            "optional": True
        },
        "start_time": {
            "type": "string",
            "optional": True
        },
        "end_time": {
            "type": "string",
            "optional": True
        }
    }

    outputs = {
        "result": {"type": "any"},
        "status": {"type": "string"}
    }

    async def execute(self, input_data: Any, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        try:
            creds = await self.get_credential("microsoft_graph_auth")
            access_token = creds.get("access_token")
            
            if not access_token:
                return {"status": "error", "error": "Microsoft Graph access token required"}

            base_url = "https://graph.microsoft.com/v1.0/me"
            headers = {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json"
            }
            
            action = self.get_config("action", "send_email")

            async with aiohttp.ClientSession() as session:
                if action == "send_email":
                    to = self.get_config("to_recipients")
                    subject = self.get_config("subject")
                    content = self.get_config("content")
                    
                    if not all([to, subject, content]):
                        return {"status": "error", "error": "to_recipients, subject, and content required"}
                    
                    recipients = [{"emailAddress": {"address": email.strip()}} for email in to.split(",") if email.strip()]
                    
                    payload = {
                        "message": {
                            "subject": subject,
                            "body": {
                                "contentType": "HTML",
                                "content": content
                            },
                            "toRecipients": recipients
                        },
                        "saveToSentItems": "true"
                    }
                    
                    url = f"{base_url}/sendMail"
                    async with session.post(url, headers=headers, json=payload) as resp:
                         if resp.status not in [200, 202]:
                            error_text = await resp.text()
                            return {"status": "error", "error": f"Outlook Error {resp.status}: {error_text}"}
                         return {"status": "success", "data": {"message": "Email sent"}}

                elif action == "create_event":
                    subject = self.get_config("subject")
                    content = self.get_config("content", "")
                    start_time = self.get_config("start_time")
                    end_time = self.get_config("end_time")
                    
                    if not all([subject, start_time, end_time]):
                        return {"status": "error", "error": "subject, start_time, and end_time required"}
                    
                    payload = {
                        "subject": subject,
                        "body": {
                            "contentType": "HTML",
                            "content": content
                        },
                        "start": {
                            "dateTime": start_time,
                            "timeZone": "UTC"
                        },
                        "end": {
                            "dateTime": end_time,
                            "timeZone": "UTC"
                        }
                    }
                    
                    url = f"{base_url}/events"
                    async with session.post(url, headers=headers, json=payload) as resp:
                        if resp.status not in [200, 201]:
                            error_text = await resp.text()
                            return {"status": "error", "error": f"Outlook Error {resp.status}: {error_text}"}
                        res_data = await resp.json()
                        return {"status": "success", "data": {"result": res_data}}

                elif action == "list_messages":
                    url = f"{base_url}/messages"
                    async with session.get(url, headers=headers) as resp:
                        if resp.status != 200:
                            error_text = await resp.text()
                            return {"status": "error", "error": f"Outlook Error {resp.status}: {error_text}"}
                        res_data = await resp.json()
                        return {"status": "success", "data": {"result": res_data.get("value", [])}}

            return {"status": "error", "error": f"Unsupported action: {action}"}

        except Exception as e:
            return {"status": "error", "error": f"Outlook Node Failed: {str(e)}"}


# ============================================
# MICROSOFT EXCEL NODE
# ============================================
@register_node("microsoft_excel_node")
class MicrosoftExcelNode(BaseNode):
    """
    Microsoft Excel Online integration via Graph API.
    """
    node_type = "microsoft_excel_node"
    version = "1.0.0"
    category = "productivity"
    credentials_required = ["microsoft_graph_auth"]

    inputs = {
        "action": {
            "type": "dropdown",
            "default": "list_rows",
            "options": ["list_rows", "add_row", "update_row", "get_worksheet"],
            "description": "Excel action"
        },
        "drive_id": {
            "type": "string",
            "optional": True
        },
        "item_id": {
            "type": "string",
            "optional": True,
            "description": "Workbook ID"
        },
        "worksheet_name": {
            "type": "string",
            "optional": True
        },
        "values": {
            "type": "any",
            "optional": True,
            "description": "Row values (array of arrays)"
        }
    }

    outputs = {
        "result": {"type": "any"},
        "status": {"type": "string"}
    }

    async def execute(self, input_data: Any, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        try:
            creds = await self.get_credential("microsoft_graph_auth")
            access_token = creds.get("access_token")
            
            if not access_token:
                return {"status": "error", "error": "Microsoft Graph access token required"}

            headers = {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json"
            }
            
            action = self.get_config("action", "list_rows")
            item_id = self.get_config("item_id")
            worksheet_name = self.get_config("worksheet_name", "Sheet1")
            
            # Simplified endpoint assuming OneDrive path for simplicity or strict ID usage
            # Production usually involves drive/item discovery first
            base_url = f"https://graph.microsoft.com/v1.0/me/drive/items/{item_id}/workbook"

            async with aiohttp.ClientSession() as session:
                if action == "list_rows":
                    if not item_id:
                        return {"status": "error", "error": "item_id (workbook ID) required"}
                        
                    url = f"{base_url}/worksheets/{worksheet_name}/usedRange"
                    async with session.get(url, headers=headers) as resp:
                        if resp.status != 200:
                            error_text = await resp.text()
                            return {"status": "error", "error": f"Excel Error {resp.status}: {error_text}"}
                        res_data = await resp.json()
                        return {"status": "success", "data": {"result": res_data.get("values", [])}}

                elif action == "add_row":
                    values = self.get_config("values") or input_data
                    if not item_id or not values:
                        return {"status": "error", "error": "item_id and values required"}
                    
                    if not isinstance(values, list):
                        values = [[values]] # Ensure array of arrays
                    elif isinstance(values, list) and not isinstance(values[0], list):
                        values = [values]
                        
                    url = f"{base_url}/worksheets/{worksheet_name}/tables/Table1/rows/add"
                    # Note: Addressing table by name 'Table1' is common but might need config
                    # Fallback to appending to range if no table
                    
                    payload = {"values": values}
                    async with session.post(url, headers=headers, json=payload) as resp:
                        if resp.status not in [200, 201]:
                            # Fallback logic could be tried here
                            error_text = await resp.text()
                            return {"status": "error", "error": f"Excel Error {resp.status}: {error_text}"}
                        res_data = await resp.json()
                        return {"status": "success", "data": {"result": res_data}}
            
            return {"status": "error", "error": f"Unsupported action: {action}"}

        except Exception as e:
            return {"status": "error", "error": f"Excel Node Failed: {str(e)}"}
