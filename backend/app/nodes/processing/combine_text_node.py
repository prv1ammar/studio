"""
Combine Text Node - Studio Standard
Batch 34: Text Processing Nodes
"""
from typing import Any, Dict, Optional, List
from ..base import BaseNode
from ..registry import register_node

@register_node("combine_text")
class CombineTextNode(BaseNode):
    """
    Concatenate multiple text sources into a single text chunk using a specified delimiter.
    Supports 2 or more text inputs.
    """
    node_type = "combine_text"
    version = "1.0.0"
    category = "text_processing"
    credentials_required = []


    properties = [
        {
            'displayName': 'Delimiter',
            'name': 'delimiter',
            'type': 'string',
            'default': ' ',
            'description': 'String used to separate the text inputs',
        },
        {
            'displayName': 'Remove Empty',
            'name': 'remove_empty',
            'type': 'boolean',
            'default': True,
            'description': 'Remove empty strings before combining',
        },
        {
            'displayName': 'Texts',
            'name': 'texts',
            'type': 'string',
            'default': '',
            'description': 'Array of texts to combine',
            'required': True,
        },
        {
            'displayName': 'Trim Whitespace',
            'name': 'trim_whitespace',
            'type': 'boolean',
            'default': True,
            'description': 'Trim whitespace from each text before combining',
        },
    ]
    inputs = {
        "texts": {
            "type": "array",
            "required": True,
            "description": "Array of texts to combine"
        },
        "delimiter": {
            "type": "string",
            "default": " ",
            "description": "String used to separate the text inputs"
        },
        "remove_empty": {
            "type": "boolean",
            "default": True,
            "description": "Remove empty strings before combining"
        },
        "trim_whitespace": {
            "type": "boolean",
            "default": True,
            "description": "Trim whitespace from each text before combining"
        }
    }

    outputs = {
        "combined_text": {"type": "string"},
        "length": {"type": "number"},
        "parts_count": {"type": "number"}
    }

    async def execute(self, input_data: Any, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        try:
            # Get texts from input
            if isinstance(input_data, list):
                texts = input_data
            elif isinstance(input_data, str):
                # If single string, combine with config texts
                config_texts = self.get_config("texts", [])
                texts = [input_data] + (config_texts if isinstance(config_texts, list) else [])
            else:
                texts = self.get_config("texts", [])

            if not texts:
                return {"status": "error", "error": "At least one text input is required"}

            # Convert all to strings
            texts = [str(t) for t in texts]

            # Get configuration
            delimiter = self.get_config("delimiter", " ")
            remove_empty = self.get_config("remove_empty", True)
            trim_whitespace = self.get_config("trim_whitespace", True)

            # Process texts
            if trim_whitespace:
                texts = [t.strip() for t in texts]

            if remove_empty:
                texts = [t for t in texts if t]

            if not texts:
                return {
                    "status": "success",
                    "data": {
                        "combined_text": "",
                        "length": 0,
                        "parts_count": 0
                    }
                }

            # Combine texts
            combined = delimiter.join(texts)

            return {
                "status": "success",
                "data": {
                    "combined_text": combined,
                    "length": len(combined),
                    "parts_count": len(texts)
                }
            }

        except Exception as e:
            return {
                "status": "error",
                "error": f"Combine Text error: {str(e)}"
            }