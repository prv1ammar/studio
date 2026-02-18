"""
HTML Parser Node - Studio Standard (Universal Method)
Batch 99: Web & Utilities (Deepening Parity)
"""
from typing import Any, Dict, Optional, List
from bs4 import BeautifulSoup
from ..base import BaseNode
from ..registry import register_node

@register_node("html_parser_node")
class HTMLParserNode(BaseNode):
    """
    Extract data from HTML strings using CSS selectors (BeautifulSoup).
    """
    node_type = "html_parser_node"
    version = "1.0.0"
    category = "utilities"
    credentials_required = []


    properties = [
        {
            'displayName': 'All Matches',
            'name': 'all_matches',
            'type': 'boolean',
            'default': False,
            'description': 'Return all matches?',
        },
        {
            'displayName': 'Attribute',
            'name': 'attribute',
            'type': 'string',
            'default': 'text',
            'options': [
                {'name': 'Text', 'value': 'text'},
                {'name': 'Innerhtml', 'value': 'innerHTML'},
                {'name': 'Outerhtml', 'value': 'outerHTML'},
                {'name': 'Href', 'value': 'href'},
                {'name': 'Src', 'value': 'src'},
            ],
            'description': 'Attribute to extract',
        },
        {
            'displayName': 'Html Content',
            'name': 'html_content',
            'type': 'string',
            'default': '',
            'description': 'HTML string to parse (from HTTP Request)',
            'required': True,
        },
        {
            'displayName': 'Selector',
            'name': 'selector',
            'type': 'string',
            'default': '',
            'description': 'CSS Selector (e.g. .class, #id)',
            'required': True,
        },
    ]
    inputs = {
        "html_content": {
            "type": "string",
            "required": True,
            "description": "HTML string to parse (from HTTP Request)"
        },
        "selector": {
            "type": "string",
            "required": True,
            "description": "CSS Selector (e.g. .class, #id)"
        },
        "attribute": {
            "type": "string",
            "default": "text",
            "options": ["text", "innerHTML", "outerHTML", "href", "src"],
            "description": "Attribute to extract"
        },
        "all_matches": {
            "type": "boolean",
            "default": False,
            "description": "Return all matches?"
        }
    }

    outputs = {
        "result": {"type": "any"},
        "status": {"type": "string"}
    }

    async def execute(self, input_data: Any, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        try:
            html = self.get_config("html_content") or str(input_data)
            selector = self.get_config("selector")
            attr = self.get_config("attribute", "text")
            all_matches = self.get_config("all_matches", False)
            
            if not html:
                return {"status": "error", "error": "html_content required"}
            if not selector:
                return {"status": "error", "error": "selector required"}
            
            soup = BeautifulSoup(html, "html.parser")
            elements = soup.select(selector)
            
            extracted = []
            
            target_list = elements if all_matches else elements[:1]
            
            for el in target_list:
                val = None
                if attr == "text":
                    val = el.get_text()
                elif attr == "innerHTML":
                    val = "".join([str(x) for x in el.content])
                elif attr == "outerHTML":
                    val = str(el)
                else:
                    val = el.get(attr)
                
                if val is not None:
                    extracted.append(val)
            
            if not all_matches:
                result = extracted[0] if extracted else None
            else:
                result = extracted
            
            return {"status": "success", "data": {"result": result}}

        except Exception as e:
            return {"status": "error", "error": f"HTML Parser Failed: {str(e)}"}