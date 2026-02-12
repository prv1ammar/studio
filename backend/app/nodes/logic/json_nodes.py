import ast
import json
from typing import Any, Dict, Optional, List
import jq
from json_repair import repair_json
from ..base import BaseNode
from ..registry import register_node

@register_node("json_query")
class JSONQueryNode(BaseNode):
    """Executes jq expressions on input JSON/Data."""
    node_type = "json_query"
    version = "1.0.0"
    category = "logic"
    
    inputs = {
        "query": {"type": "string", "description": "jq expression (e.g. .items[0].id)", "default": "."},
        "data": {"type": "object", "description": "JSON object to query"}
    }
    outputs = {
        "result": {"type": "any"},
        "status": {"type": "string"}
    }

    async def execute(self, input_data: Any, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        try:
            query = self.get_config("query", ".")
            data = input_data or self.get_config("data", {})
            
            if isinstance(data, str):
                try:
                    data = json.loads(repair_json(data))
                except:
                    pass
            
            # Root data check if it's wrapped in Studio Data object
            if isinstance(data, dict) and "data" in data and len(data) == 1:
                data = data["data"]
            
            results = jq.compile(query).input(data).all()
            final_result = results[0] if len(results) == 1 else results
            
            return {
                "status": "success",
                "data": {
                    "result": final_result
                }
            }
        except Exception as e:
            return {"status": "error", "error": f"JSON Query failed: {str(e)}"}

@register_node("json_transform")
class JSONTransformNode(BaseNode):
    """Performs bulk transformations: Select, Remove, Rename keys."""
    node_type = "json_transform"
    version = "1.0.0"
    category = "logic"
    
    inputs = {
        "operation": {"type": "string", "enum": ["select", "remove", "rename"], "default": "select"},
        "keys": {"type": "any", "description": "List of keys (for select/remove) or Dict (for rename)"},
        "data": {"type": "object"}
    }
    outputs = {
        "result": {"type": "object"},
        "status": {"type": "string"}
    }

    async def execute(self, input_data: Any, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        try:
            operation = self.get_config("operation", "select")
            keys = self.get_config("keys")
            data = input_data or self.get_config("data", {})
            
            if not isinstance(data, dict):
                return {"status": "error", "error": "Input must be a dictionary."}
            
            result = {}
            if operation == "select":
                if not isinstance(keys, list):
                    return {"status": "error", "error": "Select operation requires a list of keys."}
                result = {k: data[k] for k in keys if k in data}
            
            elif operation == "remove":
                if not isinstance(keys, list):
                    return {"status": "error", "error": "Remove operation requires a list of keys."}
                result = {k: v for k, v in data.items() if k not in keys}
                
            elif operation == "rename":
                if not isinstance(keys, dict):
                    return {"status": "error", "error": "Rename operation requires a mapping dict {old: new}."}
                result = {keys.get(k, k): v for k, v in data.items()}
                
            return {
                "status": "success",
                "data": {
                    "result": result
                }
            }
        except Exception as e:
            return {"status": "error", "error": f"JSON Transform failed: {str(e)}"}

@register_node("json_parse")
class JSONParseNode(BaseNode):
    """Parses a string or literal into a valid JSON object."""
    node_type = "json_parse"
    version = "1.0.0"
    category = "logic"
    
    inputs = {
        "text": {"type": "string", "description": "String to parse"},
        "repair": {"type": "boolean", "default": True, "description": "Attempt to fix broken JSON"}
    }
    outputs = {
        "result": {"type": "object"},
        "is_valid": {"type": "boolean"},
        "status": {"type": "string"}
    }

    async def execute(self, input_data: Any, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        try:
            text = input_data if isinstance(input_data, str) else self.get_config("text")
            should_repair = self.get_config("repair", True)
            
            if not text:
                return {"status": "error", "error": "No input text to parse."}
            
            parsed = None
            try:
                if should_repair:
                    parsed = json.loads(repair_json(text))
                else:
                    parsed = json.loads(text)
            except:
                # Fallback to literal eval for python-like literals if JSON fails
                try:
                    parsed = ast.literal_eval(text)
                except:
                    return {"status": "error", "error": "Failed to parse text as JSON or Python literal."}
                    
            return {
                "status": "success",
                "data": {
                    "result": parsed,
                    "is_valid": True
                }
            }
        except Exception as e:
            return {"status": "error", "error": f"JSON Parse failed: {str(e)}"}
