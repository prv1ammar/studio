"""
Mailgun, Postmark, SparkPost, Mandrill, Constant Contact Nodes
Batch 104: Communication Essentials - Rapid Multi-Node Creation
"""
from typing import Any, Dict, Optional
import aiohttp
from ..base import BaseNode
from ..registry import register_node

# ============================================
# MAILGUN NODE
# ============================================
@register_node("mailgun_node")
class MailgunNode(BaseNode):
    node_type = "mailgun_node"
    version = "1.0.0"
    category = "communication"
    credentials_required = ["mailgun_auth"]
    

    properties = [
        {
            'displayName': 'Operation',
            'name': 'operation',
            'type': 'options',
            'default': 'send_email',
            'options': [
                {'name': 'Send Email', 'value': 'send_email'},
                {'name': 'Get Stats', 'value': 'get_stats'},
            ],
        },
        {
            'displayName': 'From',
            'name': 'from',
            'type': 'string',
            'default': '',
        },
        {
            'displayName': 'Subject',
            'name': 'subject',
            'type': 'string',
            'default': '',
        },
        {
            'displayName': 'Text',
            'name': 'text',
            'type': 'string',
            'default': '',
        },
        {
            'displayName': 'To',
            'name': 'to',
            'type': 'string',
            'default': '',
        },
    ]
    inputs = {
        "action": {"type": "dropdown", "default": "send_email", "options": ["send_email", "get_stats"]},
        "to": {"type": "string", "optional": True},
        "from": {"type": "string", "optional": True},
        "subject": {"type": "string", "optional": True},
        "text": {"type": "string", "optional": True}
    }
    
    outputs = {"result": {"type": "any"}, "status": {"type": "string"}}
    
    async def execute(self, input_data: Any, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        try:
            creds = await self.get_credential("mailgun_auth")
            api_key = creds.get("api_key")
            domain = creds.get("domain")
            
            if not api_key or not domain:
                return {"status": "error", "error": "Mailgun API key and domain required"}
            
            action = self.get_config("action", "send_email")
            
            if action == "send_email":
                to = self.get_config("to")
                from_email = self.get_config("from")
                subject = self.get_config("subject")
                text = self.get_config("text") or str(input_data)
                
                if not all([to, from_email, subject]):
                    return {"status": "error", "error": "to, from, and subject required"}
                
                url = f"https://api.mailgun.net/v3/{domain}/messages"
                data = {
                    "from": from_email,
                    "to": to,
                    "subject": subject,
                    "text": text
                }
                
                async with aiohttp.ClientSession() as session:
                    async with session.post(url, auth=aiohttp.BasicAuth("api", api_key), data=data) as resp:
                        if resp.status != 200:
                            error_text = await resp.text()
                            return {"status": "error", "error": f"Mailgun Error {resp.status}: {error_text}"}
                        res_data = await resp.json()
                        return {"status": "success", "data": {"result": res_data}}
            
            return {"status": "error", "error": f"Unsupported action: {action}"}
        except Exception as e:
            return {"status": "error", "error": f"Mailgun Node Failed: {str(e)}"}


# ============================================
# POSTMARK NODE
# ============================================
@register_node("postmark_node")
class PostmarkNode(BaseNode):
    node_type = "postmark_node"
    version = "1.0.0"
    category = "communication"
    credentials_required = ["postmark_auth"]
    
    inputs = {
        "action": {"type": "dropdown", "default": "send_email", "options": ["send_email", "send_template"]},
        "to": {"type": "string", "optional": True},
        "from": {"type": "string", "optional": True},
        "subject": {"type": "string", "optional": True},
        "text_body": {"type": "string", "optional": True},
        "html_body": {"type": "string", "optional": True}
    }
    
    outputs = {"result": {"type": "any"}, "status": {"type": "string"}}
    
    async def execute(self, input_data: Any, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        try:
            creds = await self.get_credential("postmark_auth")
            server_token = creds.get("server_token")
            
            if not server_token:
                return {"status": "error", "error": "Postmark server token required"}
            
            url = "https://api.postmarkapp.com/email"
            headers = {
                "X-Postmark-Server-Token": server_token,
                "Content-Type": "application/json"
            }
            
            to = self.get_config("to")
            from_email = self.get_config("from")
            subject = self.get_config("subject")
            text_body = self.get_config("text_body") or str(input_data)
            
            if not all([to, from_email, subject]):
                return {"status": "error", "error": "to, from, and subject required"}
            
            payload = {
                "From": from_email,
                "To": to,
                "Subject": subject,
                "TextBody": text_body
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(url, headers=headers, json=payload) as resp:
                    if resp.status != 200:
                        error_text = await resp.text()
                        return {"status": "error", "error": f"Postmark Error {resp.status}: {error_text}"}
                    res_data = await resp.json()
                    return {"status": "success", "data": {"result": res_data}}
        except Exception as e:
            return {"status": "error", "error": f"Postmark Node Failed: {str(e)}"}


# ============================================
# SPARKPOST NODE
# ============================================
@register_node("sparkpost_node")
class SparkPostNode(BaseNode):
    node_type = "sparkpost_node"
    version = "1.0.0"
    category = "communication"
    credentials_required = ["sparkpost_auth"]
    
    inputs = {
        "action": {"type": "dropdown", "default": "send_email", "options": ["send_email"]},
        "to": {"type": "string", "optional": True},
        "from": {"type": "string", "optional": True},
        "subject": {"type": "string", "optional": True},
        "text": {"type": "string", "optional": True}
    }
    
    outputs = {"result": {"type": "any"}, "status": {"type": "string"}}
    
    async def execute(self, input_data: Any, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        try:
            creds = await self.get_credential("sparkpost_auth")
            api_key = creds.get("api_key")
            
            if not api_key:
                return {"status": "error", "error": "SparkPost API key required"}
            
            url = "https://api.sparkpost.com/api/v1/transmissions"
            headers = {
                "Authorization": api_key,
                "Content-Type": "application/json"
            }
            
            to = self.get_config("to")
            from_email = self.get_config("from", "noreply@sparkpostbox.com")
            subject = self.get_config("subject")
            text = self.get_config("text") or str(input_data)
            
            if not all([to, subject]):
                return {"status": "error", "error": "to and subject required"}
            
            payload = {
                "recipients": [{"address": to}],
                "content": {
                    "from": from_email,
                    "subject": subject,
                    "text": text
                }
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(url, headers=headers, json=payload) as resp:
                    if resp.status != 200:
                        error_text = await resp.text()
                        return {"status": "error", "error": f"SparkPost Error {resp.status}: {error_text}"}
                    res_data = await resp.json()
                    return {"status": "success", "data": {"result": res_data}}
        except Exception as e:
            return {"status": "error", "error": f"SparkPost Node Failed: {str(e)}"}


# ============================================
# MANDRILL NODE
# ============================================
@register_node("mandrill_node")
class MandrillNode(BaseNode):
    node_type = "mandrill_node"
    version = "1.0.0"
    category = "communication"
    credentials_required = ["mandrill_auth"]
    
    inputs = {
        "action": {"type": "dropdown", "default": "send_email", "options": ["send_email"]},
        "to": {"type": "string", "optional": True},
        "from_email": {"type": "string", "optional": True},
        "subject": {"type": "string", "optional": True},
        "text": {"type": "string", "optional": True}
    }
    
    outputs = {"result": {"type": "any"}, "status": {"type": "string"}}
    
    async def execute(self, input_data: Any, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        try:
            creds = await self.get_credential("mandrill_auth")
            api_key = creds.get("api_key")
            
            if not api_key:
                return {"status": "error", "error": "Mandrill API key required"}
            
            url = "https://mandrillapp.com/api/1.0/messages/send"
            
            to = self.get_config("to")
            from_email = self.get_config("from_email")
            subject = self.get_config("subject")
            text = self.get_config("text") or str(input_data)
            
            if not all([to, from_email, subject]):
                return {"status": "error", "error": "to, from_email, and subject required"}
            
            payload = {
                "key": api_key,
                "message": {
                    "text": text,
                    "subject": subject,
                    "from_email": from_email,
                    "to": [{"email": to, "type": "to"}]
                }
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=payload) as resp:
                    if resp.status != 200:
                        error_text = await resp.text()
                        return {"status": "error", "error": f"Mandrill Error {resp.status}: {error_text}"}
                    res_data = await resp.json()
                    return {"status": "success", "data": {"result": res_data}}
        except Exception as e:
            return {"status": "error", "error": f"Mandrill Node Failed: {str(e)}"}


# ============================================
# CONSTANT CONTACT NODE
# ============================================
@register_node("constant_contact_node")
class ConstantContactNode(BaseNode):
    node_type = "constant_contact_node"
    version = "1.0.0"
    category = "communication"
    credentials_required = ["constant_contact_auth"]
    
    inputs = {
        "action": {"type": "dropdown", "default": "add_contact", "options": ["add_contact", "list_contacts", "create_campaign"]},
        "email": {"type": "string", "optional": True},
        "first_name": {"type": "string", "optional": True},
        "last_name": {"type": "string", "optional": True}
    }
    
    outputs = {"result": {"type": "any"}, "status": {"type": "string"}}
    
    async def execute(self, input_data: Any, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        try:
            creds = await self.get_credential("constant_contact_auth")
            access_token = creds.get("access_token")
            
            if not access_token:
                return {"status": "error", "error": "Constant Contact access token required"}
            
            base_url = "https://api.cc.email/v3"
            headers = {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json"
            }
            
            action = self.get_config("action", "add_contact")
            
            if action == "add_contact":
                email = self.get_config("email") or str(input_data)
                first_name = self.get_config("first_name", "")
                last_name = self.get_config("last_name", "")
                
                if not email:
                    return {"status": "error", "error": "email required"}
                
                url = f"{base_url}/contacts"
                payload = {
                    "email_address": {"address": email},
                    "first_name": first_name,
                    "last_name": last_name
                }
                
                async with aiohttp.ClientSession() as session:
                    async with session.post(url, headers=headers, json=payload) as resp:
                        if resp.status not in [200, 201]:
                            error_text = await resp.text()
                            return {"status": "error", "error": f"Constant Contact Error {resp.status}: {error_text}"}
                        res_data = await resp.json()
                        return {"status": "success", "data": {"result": res_data}}
            
            elif action == "list_contacts":
                url = f"{base_url}/contacts"
                async with aiohttp.ClientSession() as session:
                    async with session.get(url, headers=headers) as resp:
                        if resp.status != 200:
                            error_text = await resp.text()
                            return {"status": "error", "error": f"Constant Contact Error {resp.status}: {error_text}"}
                        res_data = await resp.json()
                        return {"status": "success", "data": {"result": res_data.get("contacts", [])}}
            
            return {"status": "error", "error": f"Unsupported action: {action}"}
        except Exception as e:
            return {"status": "error", "error": f"Constant Contact Node Failed: {str(e)}"}