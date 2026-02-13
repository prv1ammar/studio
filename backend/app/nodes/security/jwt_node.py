"""
JWT Utility Node - Studio Standard
Batch 51: Security & Utilities
"""
from typing import Any, Dict, Optional
import time
from ...base import BaseNode
from ...registry import register_node

@register_node("jwt_node")
class JWTNode(BaseNode):
    """
    Sign or Verify JSON Web Tokens.
    """
    node_type = "jwt_node"
    version = "1.0.0"
    category = "security"

    inputs = {
        "action": {
            "type": "dropdown",
            "default": "sign",
            "options": ["sign", "verify", "decode_unverified"],
            "description": "JWT operation"
        },
        "payload": {
            "type": "json",
            "description": "JSON payload to sign"
        },
        "secret": {
            "type": "string",
            "required": True,
            "description": "JWT Secret key"
        },
        "token": {
            "type": "string",
            "description": "JWT Token to verify/decode"
        },
        "algorithm": {
            "type": "dropdown",
            "default": "HS256",
            "options": ["HS256", "HS512"],
            "description": "Signing algorithm"
        }
    }

    outputs = {
        "token": {"type": "string"},
        "payload": {"type": "json"},
        "status": {"type": "string"}
    }

    async def execute(self, input_data: Any, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        try:
            import jwt
        except ImportError:
            return {"status": "error", "error": "PyJWT library not installed. Run: pip install PyJWT"}

        try:
            action = self.get_config("action", "sign")
            secret = self.get_config("secret")
            algo = self.get_config("algorithm", "HS256")
            
            if not secret:
                 return {"status": "error", "error": "Secret key is required."}

            if action == "sign":
                payload = self.get_config("payload", {})
                if isinstance(input_data, dict):
                    payload.update(input_data)
                
                # Check for exp if not present
                if "exp" not in payload:
                     # Default to 1 hour
                     payload["exp"] = int(time.time()) + 3600
                if "iat" not in payload:
                     payload["iat"] = int(time.time())

                token = jwt.encode(payload, secret, algorithm=algo)
                return {
                    "status": "success",
                    "data": {
                        "token": token,
                        "status": "signed"
                    }
                }

            elif action == "verify":
                token = self.get_config("token") or (input_data if isinstance(input_data, str) else None)
                if not token:
                     return {"status": "error", "error": "JWT Token is required for verification."}
                
                try:
                    payload = jwt.decode(token, secret, algorithms=[algo])
                    return {
                        "status": "success",
                        "data": {
                            "payload": payload,
                            "status": "verified"
                        }
                    }
                except jwt.ExpiredSignatureError:
                     return {"status": "error", "error": "Token has expired."}
                except jwt.InvalidTokenError as e:
                     return {"status": "error", "error": f"Invalid Token: {str(e)}"}

            elif action == "decode_unverified":
                token = self.get_config("token") or (input_data if isinstance(input_data, str) else None)
                if not token:
                     return {"status": "error", "error": "JWT Token is required."}
                
                payload = jwt.decode(token, options={"verify_signature": False})
                return {
                    "status": "success",
                    "data": {
                        "payload": payload,
                        "status": "decoded"
                    }
                }

            return {"status": "error", "error": f"Unknown action: {action}"}

        except Exception as e:
            return {"status": "error", "error": f"JWT Operation failed: {str(e)}"}
