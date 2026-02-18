"""
Redis Node - Studio Standard (Universal Method)
Batch 110: Developer Tools & Databases
"""
from typing import Any, Dict, Optional
import aiohttp
from ..base import BaseNode
from ..registry import register_node

# Redis uses `redis-py` (asyncio support in redis>=4.2.0)

@register_node("redis_node")
class RedisNode(BaseNode):
    """
    Redis in-memory store integration.
    """
    node_type = "redis_node"
    version = "1.0.0"
    category = "database"
    credentials_required = ["redis_auth"]


    properties = [
        {
            'displayName': 'Operation',
            'name': 'operation',
            'type': 'options',
            'default': 'get_key',
            'options': [
                {'name': 'Get Key', 'value': 'get_key'},
                {'name': 'Set Key', 'value': 'set_key'},
                {'name': 'Del Key', 'value': 'del_key'},
                {'name': 'Incr Key', 'value': 'incr_key'},
            ],
            'description': 'Redis action',
        },
        {
            'displayName': 'Expiration',
            'name': 'expiration',
            'type': 'string',
            'default': '',
            'description': 'Expiration in seconds',
        },
        {
            'displayName': 'Key',
            'name': 'key',
            'type': 'string',
            'default': '',
        },
        {
            'displayName': 'Value',
            'name': 'value',
            'type': 'string',
            'default': '',
        },
    ]
    inputs = {
        "action": {
            "type": "dropdown",
            "default": "get_key",
            "options": ["get_key", "set_key", "del_key", "incr_key"],
            "description": "Redis action"
        },
        "key": {
            "type": "string",
            "optional": True
        },
        "value": {
            "type": "string",
            "optional": True
        },
        "expiration": {
            "type": "number",
            "optional": True,
            "description": "Expiration in seconds"
        }
    }

    outputs = {
        "result": {"type": "any"},
        "status": {"type": "string"}
    }

    async def execute(self, input_data: Any, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        try:
            import redis.asyncio as redis
        except ImportError:
            return {"status": "error", "error": "redis library not installed. Please install it to use Redis Node."}

        try:
            creds = await self.get_credential("redis_auth")
            host = creds.get("host", "localhost")
            port = int(creds.get("port", 6379))
            password = creds.get("password")
            db = int(creds.get("db", 0))
            ssl = creds.get("ssl", False)
            
            client = redis.Redis(host=host, port=port, password=password, db=db, ssl=ssl, decode_responses=True)
            
            action = self.get_config("action", "get_key")
            key = self.get_config("key")
            
            if not key:
                 return {"status": "error", "error": "key required"}

            try:
                if action == "get_key":
                    val = await client.get(key)
                    return {"status": "success", "data": {"result": val}}
                
                elif action == "set_key":
                    value = self.get_config("value")
                    ex = self.get_config("expiration")
                    if value is None: return {"status": "error", "error": "value required"}
                    
                    await client.set(key, value, ex=ex)
                    return {"status": "success", "data": {"result": "OK"}}
                
                elif action == "del_key":
                    count = await client.delete(key)
                    return {"status": "success", "data": {"result": count}}
                
                elif action == "incr_key":
                    val = await client.incr(key)
                    return {"status": "success", "data": {"result": val}}

                return {"status": "error", "error": f"Unsupported action: {action}"}

            finally:
                await client.close()

        except Exception as e:
            return {"status": "error", "error": f"Redis Node Failed: {str(e)}"}