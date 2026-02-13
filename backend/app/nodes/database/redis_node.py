"""
Redis Node - Studio Standard (Universal Method)
Batch 95: Database Connectors (n8n Critical)
"""
from typing import Any, Dict, Optional, List
import redis.asyncio as redis
from ...base import BaseNode
from ...registry import register_node

@register_node("redis_node")
class RedisNode(BaseNode):
    """
    Execute commands on a Redis database.
    Essential for caching, queues, and fast data storage.
    """
    node_type = "redis_node"
    version = "1.0.0"
    category = "database"
    credentials_required = ["redis_auth"]

    inputs = {
        "command": {
            "type": "dropdown",
            "default": "GET",
            "options": ["GET", "SET", "DEL", "HGET", "HSET", "LPUSH", "RPOP", "KEYS"],
            "description": "Redis command"
        },
        "key": {
            "type": "string",
            "required": True
        },
        "value": {
            "type": "string",
            "optional": True
        },
        "field": {
            "type": "string",
            "optional": True,
            "description": "For Hash commands"
        }
    }

    outputs = {
        "result": {"type": "any"},
        "status": {"type": "string"}
    }

    async def execute(self, input_data: Any, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        try:
            # 1. Authentication & Connection
            creds = await self.get_credential("redis_auth")
            host = creds.get("host", "localhost")
            port = int(creds.get("port", 6379))
            password = creds.get("password")
            db = int(creds.get("db", 0))
            ssl = creds.get("ssl", False)
            
            client = redis.Redis(
                host=host,
                port=port,
                password=password,
                db=db,
                ssl=ssl,
                decode_responses=True
            )
            
            # 2. Execute Command
            command = self.get_config("command", "GET")
            key = self.get_config("key")
            
            if not key and command != "KEYS": # KEYS might allow pattern in key field
                return {"status": "error", "error": "key required"}

            async with client:
                result = None
                
                if command == "GET":
                    result = await client.get(key)
                
                elif command == "SET":
                    value = self.get_config("value") or str(input_data)
                    result = await client.set(key, value)
                
                elif command == "DEL":
                    result = await client.delete(key)
                
                elif command == "HGET":
                    field = self.get_config("field")
                    if not field: return {"status": "error", "error": "field required for HGET"}
                    result = await client.hget(key, field)
                
                elif command == "HSET":
                    field = self.get_config("field")
                    value = self.get_config("value") or str(input_data)
                    if not field: return {"status": "error", "error": "field required for HSET"}
                    result = await client.hset(key, field, value)
                
                elif command == "LPUSH":
                    value = self.get_config("value") or str(input_data)
                    result = await client.lpush(key, value)
                
                elif command == "RPOP":
                    result = await client.rpop(key)
                
                elif command == "KEYS":
                    pattern = key or "*"
                    result = await client.keys(pattern)
                
                else:
                    return {"status": "error", "error": f"Unsupported command: {command}"}

                return {"status": "success", "data": {"result": result}}

        except Exception as e:
            return {"status": "error", "error": f"Redis Node Failed: {str(e)}"}
