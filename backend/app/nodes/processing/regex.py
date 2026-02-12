import re
from typing import Any, Dict, Optional, List
from ..base import BaseNode
from ..registry import register_node

@register_node("regex_extract")
class RegexNode(BaseNode):
    """
    Extracts patterns from text using regular expressions.
    """
    node_type = "regex_extract"
    version = "1.0.0"
    category = "processing"

    inputs = {
        "text": {"type": "string", "description": "Text to analyze"},
        "pattern": {"type": "string", "description": "Regex pattern to match"}
    }
    outputs = {
        "matches": {"type": "array"},
        "count": {"type": "number"},
        "result": {"type": "string"},
        "status": {"type": "string"}
    }

    async def execute(self, input_data: Any, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        try:
            text = str(input_data) if input_data is not None else self.get_config("text", "")
            pattern_str = self.get_config("pattern")
            
            if not pattern_str:
                return {"status": "error", "error": "Regex pattern is required.", "data": None}

            regex = re.compile(pattern_str)
            matches = regex.findall(text)
            
            # Normalize matches (findall can return strings or tuples)
            normalized_matches = []
            for m in matches:
                if isinstance(m, tuple):
                    normalized_matches.append({"groups": m, "full_match": "".join(m)})
                else:
                    normalized_matches.append(m)

            return {
                "status": "success",
                "data": {
                    "matches": normalized_matches,
                    "count": len(normalized_matches),
                    "result": "\n".join(str(m) for m in normalized_matches) if normalized_matches else ""
                }
            }
        except re.error as e:
            return {"status": "error", "error": f"Invalid Regex: {str(e)}", "data": None}
        except Exception as e:
            return {"status": "error", "error": f"Regex Execution Failed: {str(e)}", "data": None}
