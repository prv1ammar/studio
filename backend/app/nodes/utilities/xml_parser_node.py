"""
XML Parser Node - Studio Standard (Universal Method)
Batch 99: Web & Utilities (Deepening Parity)
"""
from typing import Any, Dict, Optional, List
import json
import xmltodict
from ..base import BaseNode
from ..registry import register_node

@register_node("xml_parser_node")
class XMLParserNode(BaseNode):
    """
    Convert XML string to JSON/Dict.
    """
    node_type = "xml_parser_node"
    version = "1.0.0"
    category = "utilities"
    credentials_required = []


    properties = [
        {
            'displayName': 'Options',
            'name': 'options',
            'type': 'options',
            'default': 'parse',
            'options': [
                {'name': 'Parse', 'value': 'parse'},
                {'name': 'Unparse', 'value': 'unparse'},
            ],
            'description': 'Parse (XML -> JSON) or Unparse (JSON -> XML)',
        },
        {
            'displayName': 'Xml Content',
            'name': 'xml_content',
            'type': 'string',
            'default': '',
            'description': 'XML string to parse',
            'required': True,
        },
    ]
    inputs = {
        "xml_content": {
            "type": "string",
            "required": True,
            "description": "XML string to parse"
        },
        "options": {
            "type": "dropdown",
            "default": "parse",
            "options": ["parse", "unparse"],
            "description": "Parse (XML -> JSON) or Unparse (JSON -> XML)"
        }
    }

    outputs = {
        "result": {"type": "any"},
        "status": {"type": "string"}
    }

    async def execute(self, input_data: Any, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        try:
            content = self.get_config("xml_content") or str(input_data)
            action = self.get_config("options", "parse")
            
            if not content:
                return {"status": "error", "error": "xml_content required"}

            if action == "parse":
                data_dict = xmltodict.parse(content)
                return {"status": "success", "data": {"result": data_dict}}
            
            elif action == "unparse":
                # Expecting JSON/Dict input in content
                try:
                    data = json.loads(content) if isinstance(content, str) else content
                except:
                     data = content # Fallback
                
                xml_str = xmltodict.unparse(data)
                return {"status": "success", "data": {"result": xml_str}}
            
            return {"status": "error", "error": f"Unsupported action: {action}"}

        except Exception as e:
            return {"status": "error", "error": f"XML Parser Failed: {str(e)}"}