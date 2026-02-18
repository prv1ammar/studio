"""
Hashing Utility Node - Studio Standard
Batch 51: Security & Utilities
"""
import hashlib
from typing import Any, Dict, Optional
from ..base import BaseNode
from ..registry import register_node

@register_node("hash_node")
class HashNode(BaseNode):
    """
    Generate cryptographic hashes for text or data.
    Supports: MD5, SHA-1, SHA-256, SHA-512.
    """
    node_type = "hash_node"
    version = "1.0.0"
    category = "security"


    properties = [
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
            'description': 'Hashing algorithm',
        },
        {
            'displayName': 'Salt',
            'name': 'salt',
            'type': 'string',
            'default': '',
            'description': 'Optional salt to append before hashing',
        },
        {
            'displayName': 'Text',
            'name': 'text',
            'type': 'string',
            'default': '',
            'description': 'Text to hash',
            'required': True,
        },
    ]
    inputs = {
        "algorithm": {
            "type": "dropdown",
            "default": "sha256",
            "options": ["md5", "sha1", "sha256", "sha512"],
            "description": "Hashing algorithm"
        },
        "text": {
            "type": "string",
            "required": True,
            "description": "Text to hash"
        },
        "salt": {
            "type": "string",
            "optional": True,
            "description": "Optional salt to append before hashing"
        }
    }

    outputs = {
        "hash": {"type": "string"},
        "status": {"type": "string"}
    }

    async def execute(self, input_data: Any, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        try:
            algo = self.get_config("algorithm", "sha256").lower()
            text = self.get_config("text")
            salt = self.get_config("salt", "")

            # Dynamic Override
            if isinstance(input_data, str) and input_data:
                text = input_data

            if not text:
                return {"status": "error", "error": "Input text is required for hashing."}

            combined = f"{text}{salt}".encode('utf-8')
            
            if algo == "md5":
                result = hashlib.md5(combined).hexdigest()
            elif algo == "sha1":
                result = hashlib.sha1(combined).hexdigest()
            elif algo == "sha256":
                result = hashlib.sha256(combined).hexdigest()
            elif algo == "sha512":
                result = hashlib.sha512(combined).hexdigest()
            else:
                 return {"status": "error", "error": f"Unsupported algorithm: {algo}"}

            return {
                "status": "success",
                "data": {
                    "hash": result,
                    "algorithm": algo,
                    "status": "hashed"
                }
            }

        except Exception as e:
            return {"status": "error", "error": f"Hashing failed: {str(e)}"}