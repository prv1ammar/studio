"""
Parse JSON Data Node - Studio Standard
Batch 31: Data Processing Nodes
"""
import json
from typing import Any, Dict, Optional, List
from ..base import BaseNode
from ..registry import register_node

@register_node("parse_json_data")
class ParseJSONDataNode(BaseNode):
    """
    Parse and query JSON data using JQ syntax.
    Supports filtering, transforming, and extracting data from JSON structures.
    """
    node_type = "parse_json_data"
    version = "1.0.0"
    category = "data_processing"
    credentials_required = []


    properties = [
        {
            'displayName': 'Auto Repair',
            'name': 'auto_repair',
            'type': 'boolean',
            'default': True,
            'description': 'Automatically repair malformed JSON',
        },
        {
            'displayName': 'Input Value',
            'name': 'input_value',
            'type': 'string',
            'default': '',
            'description': 'JSON string, object, or Data to parse',
            'required': True,
        },
        {
            'displayName': 'Query',
            'name': 'query',
            'type': 'string',
            'default': '',
            'description': 'JQ query to filter/transform the data (e.g., '.items[]', '.name')',
            'required': True,
        },
        {
            'displayName': 'Return As List',
            'name': 'return_as_list',
            'type': 'boolean',
            'default': True,
            'description': 'Return results as a list even for single values',
        },
    ]
    inputs = {
        "input_value": {
            "type": "any",
            "required": True,
            "description": "JSON string, object, or Data to parse"
        },
        "query": {
            "type": "string",
            "required": True,
            "description": "JQ query to filter/transform the data (e.g., '.items[]', '.name')"
        },
        "auto_repair": {
            "type": "boolean",
            "default": True,
            "description": "Automatically repair malformed JSON"
        },
        "return_as_list": {
            "type": "boolean",
            "default": True,
            "description": "Return results as a list even for single values"
        }
    }

    outputs = {
        "filtered_data": {"type": "array"},
        "count": {"type": "number"},
        "query_used": {"type": "string"}
    }

    async def execute(self, input_data: Any, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        try:
            # Import dependencies
            try:
                import jq
                from json_repair import repair_json
            except ImportError as e:
                missing = "jq" if "jq" in str(e) else "json-repair"
                return {
                    "status": "error",
                    "error": f"{missing} not installed. Run: pip install {missing}"
                }

            # Get input value
            to_filter = input_data if input_data is not None else self.get_config("input_value")
            query = self.get_config("query", ".")
            auto_repair = self.get_config("auto_repair", True)
            return_as_list = self.get_config("return_as_list", True)

            if not to_filter:
                return {
                    "status": "success",
                    "data": {
                        "filtered_data": [],
                        "count": 0,
                        "query_used": query
                    }
                }

            # Parse input data
            parsed_data = self._parse_input(to_filter, auto_repair)

            # Convert to JSON string for jq processing
            if isinstance(parsed_data, list):
                json_str = json.dumps(parsed_data)
            else:
                json_str = json.dumps(parsed_data)

            # Apply JQ query
            try:
                results = jq.compile(query).input_text(json_str).all()
            except Exception as e:
                return {
                    "status": "error",
                    "error": f"JQ query error: {str(e)}. Query: '{query}'"
                }

            # Format results
            if not return_as_list and len(results) == 1:
                filtered_data = results[0]
            else:
                filtered_data = results

            return {
                "status": "success",
                "data": {
                    "filtered_data": filtered_data,
                    "count": len(results) if isinstance(results, list) else 1,
                    "query_used": query
                }
            }

        except Exception as e:
            return {
                "status": "error",
                "error": f"Parse JSON Data error: {str(e)}"
            }

    def _parse_input(self, input_value: Any, auto_repair: bool = True) -> Any:
        """Parse various input formats to JSON-compatible data."""
        # Handle list of inputs
        if isinstance(input_value, list):
            return [self._parse_single_input(item, auto_repair) for item in input_value]
        else:
            return self._parse_single_input(input_value, auto_repair)

    def _parse_single_input(self, value: Any, auto_repair: bool = True) -> Any:
        """Parse a single input value."""
        # If it's already a dict or list, return as-is
        if isinstance(value, (dict, list)):
            return value

        # If it's a string, try to parse as JSON
        if isinstance(value, str):
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                if auto_repair:
                    try:
                        from json_repair import repair_json
                        repaired = str(repair_json(value))
                        return json.loads(repaired)
                    except:
                        # If repair fails, return as string
                        return value
                else:
                    return value

        # For other types, convert to string
        return str(value)