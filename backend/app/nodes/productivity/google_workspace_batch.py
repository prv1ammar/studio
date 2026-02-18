"""
Google Productivity Nodes - Studio Standard (Universal Method)
Batch 105: Productivity Suite
"""
from typing import Any, Dict, Optional, List
import aiohttp
from ..base import BaseNode
from ..registry import register_node

# ============================================
# GOOGLE CALENDAR NODE
# ============================================
@register_node("google_calendar_node")
class GoogleCalendarNode(BaseNode):
    """
    Google Calendar integration for event management.
    """
    node_type = "google_calendar_node"
    version = "1.0.0"
    category = "productivity"
    credentials_required = ["google_calendar_auth"]


    properties = [
        {
            'displayName': 'Operation',
            'name': 'operation',
            'type': 'options',
            'default': 'list_events',
            'options': [
                {'name': 'List Events', 'value': 'list_events'},
                {'name': 'Create Event', 'value': 'create_event'},
                {'name': 'Update Event', 'value': 'update_event'},
                {'name': 'Delete Event', 'value': 'delete_event'},
                {'name': 'Get Event', 'value': 'get_event'},
                {'name': 'List Calendars', 'value': 'list_calendars'},
            ],
            'description': 'Calendar action',
        },
        {
            'displayName': 'Attendees',
            'name': 'attendees',
            'type': 'string',
            'default': '',
            'description': 'Comma separated emails',
        },
        {
            'displayName': 'Calendar Id',
            'name': 'calendar_id',
            'type': 'string',
            'default': 'primary',
        },
        {
            'displayName': 'Description',
            'name': 'description',
            'type': 'string',
            'default': '',
        },
        {
            'displayName': 'End Time',
            'name': 'end_time',
            'type': 'string',
            'default': '',
            'description': 'ISO 8601 format',
        },
        {
            'displayName': 'Event Id',
            'name': 'event_id',
            'type': 'string',
            'default': '',
        },
        {
            'displayName': 'Start Time',
            'name': 'start_time',
            'type': 'string',
            'default': '',
            'description': 'ISO 8601 format (e.g. 2024-01-01T10:00:00Z)',
        },
        {
            'displayName': 'Summary',
            'name': 'summary',
            'type': 'string',
            'default': '',
            'description': 'Event title',
        },
    ]
    inputs = {
        "action": {
            "type": "dropdown",
            "default": "list_events",
            "options": ["list_events", "create_event", "update_event", "delete_event", "get_event", "list_calendars"],
            "description": "Calendar action"
        },
        "calendar_id": {
            "type": "string",
            "default": "primary",
            "optional": True
        },
        "summary": {
            "type": "string",
            "optional": True,
            "description": "Event title"
        },
        "description": {
            "type": "string",
            "optional": True
        },
        "start_time": {
            "type": "string",
            "optional": True,
            "description": "ISO 8601 format (e.g. 2024-01-01T10:00:00Z)"
        },
        "end_time": {
            "type": "string",
            "optional": True,
            "description": "ISO 8601 format"
        },
        "event_id": {
            "type": "string",
            "optional": True
        },
        "attendees": {
            "type": "string",
            "optional": True,
            "description": "Comma separated emails"
        }
    }

    outputs = {
        "result": {"type": "any"},
        "status": {"type": "string"}
    }

    async def execute(self, input_data: Any, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        try:
            creds = await self.get_credential("google_calendar_auth")
            access_token = creds.get("access_token")
            
            if not access_token:
                return {"status": "error", "error": "Google Calendar access token required"}

            base_url = "https://www.googleapis.com/calendar/v3"
            headers = {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json"
            }
            
            action = self.get_config("action", "list_events")
            calendar_id = self.get_config("calendar_id", "primary")

            async with aiohttp.ClientSession() as session:
                if action == "list_events":
                    url = f"{base_url}/calendars/{calendar_id}/events"
                    async with session.get(url, headers=headers) as resp:
                        if resp.status != 200:
                            error_text = await resp.text()
                            return {"status": "error", "error": f"Google Calendar Error {resp.status}: {error_text}"}
                        res_data = await resp.json()
                        return {"status": "success", "data": {"result": res_data.get("items", [])}}

                elif action == "create_event":
                    summary = self.get_config("summary")
                    start_time = self.get_config("start_time")
                    end_time = self.get_config("end_time")
                    description = self.get_config("description", "")
                    attendees_str = self.get_config("attendees", "")
                    
                    if not summary or not start_time or not end_time:
                        return {"status": "error", "error": "summary, start_time, and end_time required"}
                    
                    payload = {
                        "summary": summary,
                        "description": description,
                        "start": {"dateTime": start_time},
                        "end": {"dateTime": end_time}
                    }
                    
                    if attendees_str:
                        payload["attendees"] = [{"email": email.strip()} for email in attendees_str.split(",") if email.strip()]
                    
                    url = f"{base_url}/calendars/{calendar_id}/events"
                    async with session.post(url, headers=headers, json=payload) as resp:
                        if resp.status != 200:
                            error_text = await resp.text()
                            return {"status": "error", "error": f"Google Calendar Error {resp.status}: {error_text}"}
                        res_data = await resp.json()
                        return {"status": "success", "data": {"result": res_data}}

                elif action == "get_event":
                    event_id = self.get_config("event_id") or str(input_data)
                    if not event_id:
                        return {"status": "error", "error": "event_id required"}
                    
                    url = f"{base_url}/calendars/{calendar_id}/events/{event_id}"
                    async with session.get(url, headers=headers) as resp:
                        if resp.status != 200:
                            error_text = await resp.text()
                            return {"status": "error", "error": f"Google Calendar Error {resp.status}: {error_text}"}
                        res_data = await resp.json()
                        return {"status": "success", "data": {"result": res_data}}

                elif action == "delete_event":
                    event_id = self.get_config("event_id") or str(input_data)
                    if not event_id:
                        return {"status": "error", "error": "event_id required"}
                    
                    url = f"{base_url}/calendars/{calendar_id}/events/{event_id}"
                    async with session.delete(url, headers=headers) as resp:
                        if resp.status != 204:
                            error_text = await resp.text()
                            return {"status": "error", "error": f"Google Calendar Error {resp.status}: {error_text}"}
                        return {"status": "success", "data": {"result": {"message": "Event deleted"}}}
                
                elif action == "list_calendars":
                     url = f"https://www.googleapis.com/calendar/v3/users/me/calendarList"
                     async with session.get(url, headers=headers) as resp:
                        if resp.status != 200:
                            error_text = await resp.text()
                            return {"status": "error", "error": f"Google Calendar Error {resp.status}: {error_text}"}
                        res_data = await resp.json()
                        return {"status": "success", "data": {"result": res_data.get("items", [])}}

            return {"status": "error", "error": f"Unsupported action: {action}"}

        except Exception as e:
            return {"status": "error", "error": f"Google Calendar Node Failed: {str(e)}"}


# ============================================
# GOOGLE DOCS NODE
# ============================================
@register_node("google_docs_node")
class GoogleDocsNode(BaseNode):
    """
    Google Docs integration for document management.
    """
    node_type = "google_docs_node"
    version = "1.0.0"
    category = "productivity"
    credentials_required = ["google_docs_auth"]

    inputs = {
        "action": {
            "type": "dropdown",
            "default": "create_document",
            "options": ["create_document", "get_document", "append_text", "replace_text"],
            "description": "Google Docs action"
        },
        "title": {
            "type": "string",
            "optional": True
        },
        "document_id": {
            "type": "string",
            "optional": True
        },
        "text": {
            "type": "string",
            "optional": True
        },
        "find_text": {
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
            creds = await self.get_credential("google_docs_auth")
            access_token = creds.get("access_token")
            
            if not access_token:
                return {"status": "error", "error": "Google Docs access token required"}

            base_url = "https://docs.googleapis.com/v1/documents"
            headers = {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json"
            }
            
            action = self.get_config("action", "create_document")

            async with aiohttp.ClientSession() as session:
                if action == "create_document":
                    title = self.get_config("title", "Untitled Document")
                    payload = {"title": title}
                    
                    async with session.post(base_url, headers=headers, json=payload) as resp:
                        if resp.status != 200:
                            error_text = await resp.text()
                            return {"status": "error", "error": f"Google Docs Error {resp.status}: {error_text}"}
                        res_data = await resp.json()
                        
                        # Apply initial text if provided
                        text = self.get_config("text")
                        if text:
                            doc_id = res_data.get("documentId")
                            update_url = f"{base_url}/{doc_id}:batchUpdate"
                            update_payload = {
                                "requests": [
                                    {
                                        "insertText": {
                                            "text": text,
                                            "endOfSegmentLocation": {"segmentId": ""}
                                        }
                                    }
                                ]
                            }
                            await session.post(update_url, headers=headers, json=update_payload)
                            
                        return {"status": "success", "data": {"result": res_data}}

                elif action == "get_document":
                    document_id = self.get_config("document_id") or str(input_data)
                    if not document_id:
                         return {"status": "error", "error": "document_id required"}
                         
                    url = f"{base_url}/{document_id}"
                    async with session.get(url, headers=headers) as resp:
                        if resp.status != 200:
                            error_text = await resp.text()
                            return {"status": "error", "error": f"Google Docs Error {resp.status}: {error_text}"}
                        res_data = await resp.json()
                        return {"status": "success", "data": {"result": res_data}}

                elif action == "append_text":
                    document_id = self.get_config("document_id")
                    text = self.get_config("text")
                    
                    if not document_id or not text:
                        return {"status": "error", "error": "document_id and text required"}
                    
                    url = f"{base_url}/{document_id}:batchUpdate"
                    payload = {
                        "requests": [
                            {
                                "insertText": {
                                    "text": text,
                                    "endOfSegmentLocation": {"segmentId": ""}
                                }
                            }
                        ]
                    }
                    
                    async with session.post(url, headers=headers, json=payload) as resp:
                        if resp.status != 200:
                            error_text = await resp.text()
                            return {"status": "error", "error": f"Google Docs Error {resp.status}: {error_text}"}
                        res_data = await resp.json()
                        return {"status": "success", "data": {"result": res_data}}

                elif action == "replace_text":
                    document_id = self.get_config("document_id")
                    find_text = self.get_config("find_text")
                    replace_text = self.get_config("text")
                    
                    if not all([document_id, find_text, replace_text]):
                         return {"status": "error", "error": "document_id, find_text, and text (replace) required"}

                    url = f"{base_url}/{document_id}:batchUpdate"
                    payload = {
                        "requests": [
                            {
                                "replaceAllText": {
                                    "containsText": {
                                        "text": find_text,
                                        "matchCase": True
                                    },
                                    "replaceText": replace_text
                                }
                            }
                        ]
                    }
                    async with session.post(url, headers=headers, json=payload) as resp:
                         if resp.status != 200:
                            error_text = await resp.text()
                            return {"status": "error", "error": f"Google Docs Error {resp.status}: {error_text}"}
                         res_data = await resp.json()
                         return {"status": "success", "data": {"result": res_data}}

            return {"status": "error", "error": f"Unsupported action: {action}"}

        except Exception as e:
            return {"status": "error", "error": f"Google Docs Node Failed: {str(e)}"}