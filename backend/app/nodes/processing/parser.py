from typing import Any, Dict, Optional
from ..base import BaseNode
from ..registry import register_node

@register_node("text_parser")
class TextParserNode(BaseNode):
    """
    Extracts or formats text using a template or stringification mode.
    """
    node_type = "text_parser"
    version = "1.0.0"
    category = "processing"


    properties = [
        {
            'displayName': 'Input Data',
            'name': 'input_data',
            'type': 'string',
            'default': '',
            'description': 'Data to parse or stringify',
        },
        {
            'displayName': 'Mode',
            'name': 'mode',
            'type': 'string',
            'default': 'Parser',
        },
        {
            'displayName': 'Separator',
            'name': 'separator',
            'type': 'string',
            'default': '
',
            'description': 'Separator for multiple items',
        },
        {
            'displayName': 'Template',
            'name': 'template',
            'type': 'string',
            'default': 'Text: {text}',
            'description': 'Template with {key} variables',
        },
    ]
    inputs = {
        "input_data": {"type": "any", "description": "Data to parse or stringify"},
        "mode": {"type": "string", "enum": ["Parser", "Stringify"], "default": "Parser"},
        "template": {"type": "string", "default": "Text: {text}", "description": "Template with {key} variables"},
        "separator": {"type": "string", "default": "\n", "description": "Separator for multiple items"}
    }
    outputs = {
        "result": {"type": "string"},
        "status": {"type": "string"}
    }

    async def execute(self, input_data: Any, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        try:
            mode = self.get_config("mode", "Parser")
            data = input_data if input_data is not None else self.get_config("input_data")
            
            if data is None:
                return {"status": "error", "error": "No input data provided."}

            if mode == "Stringify":
                if isinstance(data, (dict, list)):
                    import json
                    result = json.dumps(data, indent=2)
                else:
                    result = str(data)
            else:
                template = self.get_config("template", "{text}")
                sep = self.get_config("separator", "\n")
                
                if isinstance(data, list):
                    lines = []
                    for item in data:
                        if isinstance(item, dict):
                            lines.append(template.format(**item))
                        else:
                            lines.append(template.format(text=str(item)))
                    result = sep.join(lines)
                elif isinstance(data, dict):
                    result = template.format(**data)
                else:
                    result = template.format(text=str(data))

            return {
                "status": "success",
                "data": {"result": result}
            }
        except Exception as e:
            return {"status": "error", "error": f"Parsing Failed: {str(e)}"}