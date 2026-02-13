"""
Regex Precision Node - Studio Standard
Batch 50: Golden Batch (Intelligence Expansion)
"""
import re
from typing import Any, Dict, Optional, List
from ...base import BaseNode
from ...registry import register_node

@register_node("regex_node")
class RegexNode(BaseNode):
    """
    Powerful regex engine for pattern extraction, replacement, and splitting.
    """
    node_type = "regex_node"
    version = "1.1.0"
    category = "logic"

    inputs = {
        "action": {
            "type": "dropdown",
            "default": "findall",
            "options": ["findall", "search", "replace", "split"],
            "description": "Regex operation"
        },
        "text": {
            "type": "string",
            "required": True,
            "description": "Input text to process"
        },
        "pattern": {
            "type": "string",
            "required": True,
            "description": "Regex pattern"
        },
        "replacement": {
            "type": "string",
            "optional": True,
            "description": "Replacement text (for 'replace' action)"
        },
        "flags": {
            "type": "dropdown",
            "default": "NONE",
            "options": ["NONE", "IGNORECASE", "MULTILINE", "DOTALL"],
            "description": "Regex flags"
        }
    }

    outputs = {
        "result": {"type": "string"},
        "matches": {"type": "array"},
        "count": {"type": "number"},
        "groups": {"type": "dict"}
    }

    async def execute(self, input_data: Any, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        try:
            action = self.get_config("action", "findall")
            text = self.get_config("text")
            pattern_str = self.get_config("pattern")
            
            # Dynamic Override
            if isinstance(input_data, str) and input_data:
                text = input_data
            elif isinstance(input_data, dict):
                text = input_data.get("text") or text
                pattern_str = input_data.get("pattern") or pattern_str

            if not text or not pattern_str:
                return {"status": "error", "error": "Text and Pattern are required."}

            # Map flags
            flags_map = {
                "NONE": 0,
                "IGNORECASE": re.IGNORECASE,
                "MULTILINE": re.MULTILINE,
                "DOTALL": re.DOTALL
            }
            flag = flags_map.get(self.get_config("flags", "NONE"), 0)

            regex = re.compile(pattern_str, flag)
            
            result_data = {}

            if action == "findall":
                matches = regex.findall(text)
                # Findall returns groups if pattern has groups
                result_data = {
                    "matches": matches,
                    "count": len(matches),
                    "result": str(matches[0]) if matches else ""
                }

            elif action == "search":
                match = regex.search(text)
                if match:
                    result_data = {
                        "result": match.group(0),
                        "groups": match.groupdict() if match.groupdict() else list(match.groups()),
                        "matches": [match.group(0)],
                        "count": 1
                    }
                else:
                    result_data = {"result": "", "count": 0, "matches": []}

            elif action == "replace":
                replacement = self.get_config("replacement", "")
                new_text = regex.sub(replacement, text)
                result_data = {
                    "result": new_text,
                    "status": "replaced"
                }

            elif action == "split":
                parts = regex.split(text)
                result_data = {
                    "matches": parts,
                    "count": len(parts),
                    "result": parts[0] if parts else ""
                }

            return {
                "status": "success",
                "data": result_data
            }

        except re.error as e:
            return {"status": "error", "error": f"Regex Syntax Error: {str(e)}"}
        except Exception as e:
            return {"status": "error", "error": f"Regex Execution Failed: {str(e)}"}
