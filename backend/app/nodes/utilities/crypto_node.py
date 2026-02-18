"""
Crypto Node - Studio Standard (Universal Method)
Batch 111: Utilities & Data Processing
"""
from typing import Any, Dict, Optional
import hashlib
import hmac
import base64
from ..base import BaseNode
from ..registry import register_node

@register_node("crypto_node")
class CryptoNode(BaseNode):
    """
    Cryptographic functions: Hash, HMAC, Base64.
    """
    node_type = "crypto_node"
    version = "1.0.0"
    category = "utilities"
    credentials_required = []


    properties = [
        {
            'displayName': 'Operation',
            'name': 'operation',
            'type': 'options',
            'default': 'hash',
            'options': [
                {'name': 'Hash', 'value': 'hash'},
                {'name': 'Hmac', 'value': 'hmac'},
                {'name': 'Base64 Encode', 'value': 'base64_encode'},
                {'name': 'Base64 Decode', 'value': 'base64_decode'},
            ],
            'description': 'Crypto action',
        },
        {
            'displayName': 'Algorithm',
            'name': 'algorithm',
            'type': 'options',
            'default': 'sha256',
            'options': [
                {'name': 'Md5', 'value': 'md5'},
                {'name': 'Sha1', 'value': 'sha1'},
                {'name': 'Sha256', 'value': 'sha256'},
                {'name': 'Sha512', 'value': 'sha512'},
            ],
        },
        {
            'displayName': 'Secret',
            'name': 'secret',
            'type': 'string',
            'default': '',
            'description': 'Key for HMAC',
        },
        {
            'displayName': 'Value',
            'name': 'value',
            'type': 'string',
            'default': '',
            'required': True,
        },
    ]
    inputs = {
        "action": {
            "type": "dropdown",
            "default": "hash",
            "options": ["hash", "hmac", "base64_encode", "base64_decode"],
            "description": "Crypto action"
        },
        "value": {
            "type": "string",
            "required": True
        },
        "algorithm": {
            "type": "dropdown",
            "default": "sha256",
            "options": ["md5", "sha1", "sha256", "sha512"],
            "optional": True
        },
        "secret": {
            "type": "string",
            "optional": True,
            "description": "Key for HMAC"
        }
    }

    outputs = {
        "result": {"type": "any"},
        "status": {"type": "string"}
    }

    async def execute(self, input_data: Any, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        try:
            value = self.get_config("value")
            if value is None: value = str(input_data)
            
            action = self.get_config("action", "hash")
            algo = self.get_config("algorithm", "sha256")
            
            key = self.get_config("secret")
            
            if action == "hash":
                h = None
                if algo == "md5": h = hashlib.md5()
                elif algo == "sha1": h = hashlib.sha1()
                elif algo == "sha256": h = hashlib.sha256()
                elif algo == "sha512": h = hashlib.sha512()
                else: h = hashlib.sha256()
                
                h.update(value.encode('utf-8'))
                return {"status": "success", "data": {"result": h.hexdigest()}}

            elif action == "hmac":
                if not key: return {"status": "error", "error": "secret required for HMAC"}
                
                digest = None
                if algo == "md5": digest = hashlib.md5
                elif algo == "sha1": digest = hashlib.sha1
                elif algo == "sha256": digest = hashlib.sha256
                elif algo == "sha512": digest = hashlib.sha512
                else: digest = hashlib.sha256
                
                h = hmac.new(key.encode('utf-8'), value.encode('utf-8'), digest)
                return {"status": "success", "data": {"result": h.hexdigest()}}

            elif action == "base64_encode":
                b = base64.b64encode(value.encode('utf-8')).decode('utf-8')
                return {"status": "success", "data": {"result": b}}

            elif action == "base64_decode":
                try:
                    s = base64.b64decode(value).decode('utf-8')
                    return {"status": "success", "data": {"result": s}}
                except Exception as e:
                    return {"status": "error", "error": f"Base64 Decode Error: {str(e)}"}

            return {"status": "error", "error": f"Unsupported action: {action}"}

        except Exception as e:
            return {"status": "error", "error": f"Crypto Node Failed: {str(e)}"}