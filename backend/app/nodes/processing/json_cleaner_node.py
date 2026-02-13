"""
JSON Cleaner Node - Studio Standard
Batch 31: Data Processing Nodes
"""
import json
import unicodedata
from typing import Any, Dict, Optional
from ...base import BaseNode
from ...registry import register_node

@register_node("json_cleaner")
class JSONCleanerNode(BaseNode):
    """
    Cleans messy JSON strings produced by LLMs to be fully JSON-compliant.
    Removes control characters, normalizes Unicode, and repairs malformed JSON.
    """
    node_type = "json_cleaner"
    version = "1.0.0"
    category = "data_processing"
    credentials_required = []

    inputs = {
        "json_str": {
            "type": "string",
            "required": True,
            "description": "The JSON string to be cleaned"
        },
        "remove_control_chars": {
            "type": "boolean",
            "default": True,
            "description": "Remove control characters from the JSON string"
        },
        "normalize_unicode": {
            "type": "boolean",
            "default": True,
            "description": "Normalize Unicode characters in the JSON string"
        },
        "validate_json": {
            "type": "boolean",
            "default": True,
            "description": "Validate the JSON string to ensure it is well-formed"
        },
        "auto_repair": {
            "type": "boolean",
            "default": True,
            "description": "Automatically repair malformed JSON using json-repair"
        }
    }

    outputs = {
        "cleaned_json": {"type": "string"},
        "parsed_data": {"type": "object"},
        "is_valid": {"type": "boolean"}
    }

    def __init__(self, config=None):
        super().__init__(config)
        # Create translation table for control character removal
        self.translation_table = str.maketrans("", "", "".join(chr(i) for i in range(32)) + chr(127))

    async def execute(self, input_data: Any, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        try:
            # Get JSON string from input
            json_str = input_data if isinstance(input_data, str) else self.get_config("json_str", "")
            
            if not json_str:
                return {"status": "error", "error": "JSON string is required"}

            # Get configuration
            remove_control_chars = self.get_config("remove_control_chars", True)
            normalize_unicode = self.get_config("normalize_unicode", True)
            validate_json = self.get_config("validate_json", True)
            auto_repair = self.get_config("auto_repair", True)

            # Extract JSON from string (find first { to last })
            start = json_str.find("{")
            end = json_str.rfind("}")
            
            if start == -1 or end == -1:
                # Try array format
                start = json_str.find("[")
                end = json_str.rfind("]")
                
            if start == -1 or end == -1:
                return {
                    "status": "error",
                    "error": "Invalid JSON string: Missing '{' or '}' (or '[' or ']')"
                }

            json_str = json_str[start:end + 1]

            # Apply cleaning operations
            if remove_control_chars:
                json_str = self._remove_control_characters(json_str)
            
            if normalize_unicode:
                json_str = self._normalize_unicode(json_str)

            # Validate before repair
            is_valid = False
            if validate_json:
                is_valid = self._validate_json(json_str)

            # Auto-repair if needed
            if auto_repair and not is_valid:
                try:
                    from json_repair import repair_json
                    json_str = str(repair_json(json_str))
                except ImportError:
                    return {
                        "status": "error",
                        "error": "json-repair not installed. Run: pip install json-repair"
                    }

            # Final validation and parsing
            try:
                parsed_data = json.loads(json_str)
                is_valid = True
            except json.JSONDecodeError as e:
                return {
                    "status": "error",
                    "error": f"Failed to parse JSON after cleaning: {str(e)}",
                    "data": {
                        "cleaned_json": json_str,
                        "is_valid": False
                    }
                }

            return {
                "status": "success",
                "data": {
                    "cleaned_json": json_str,
                    "parsed_data": parsed_data,
                    "is_valid": is_valid
                }
            }

        except Exception as e:
            return {
                "status": "error",
                "error": f"JSON Cleaner error: {str(e)}"
            }

    def _remove_control_characters(self, s: str) -> str:
        """Remove control characters from the string."""
        return s.translate(self.translation_table)

    def _normalize_unicode(self, s: str) -> str:
        """Normalize Unicode characters in the string."""
        return unicodedata.normalize("NFC", s)

    def _validate_json(self, s: str) -> bool:
        """Validate the JSON string."""
        try:
            json.loads(s)
            return True
        except json.JSONDecodeError:
            return False
