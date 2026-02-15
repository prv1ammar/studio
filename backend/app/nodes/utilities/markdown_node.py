"""
Markdown Node - Studio Standard (Universal Method)
Batch 111: Utilities & Data Processing
"""
from typing import Any, Dict, Optional
import markdown
import html2text
from ...base import BaseNode
from ...registry import register_node

@register_node("markdown_node")
class MarkdownNode(BaseNode):
    """
    Convert between Markdown and HTML.
    """
    node_type = "markdown_node"
    version = "1.0.0"
    category = "utilities"
    credentials_required = []

    inputs = {
        "action": {
            "type": "dropdown",
            "default": "markdown_to_html",
            "options": ["markdown_to_html", "html_to_markdown"],
            "description": "Conversion"
        },
        "content": {
            "type": "string",
            "optional": True
        }
    }

    outputs = {
        "result": {"type": "any"},
        "status": {"type": "string"}
    }

    async def execute(self, input_data: Any, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        try:
            content = self.get_config("content") or str(input_data)
            action = self.get_config("action", "markdown_to_html")
            
            if action == "markdown_to_html":
                # Requires 'markdown' library
                try:
                    html = markdown.markdown(content)
                    return {"status": "success", "data": {"result": html}}
                except ImportError:
                    return {"status": "error", "error": "markdown library required"}

            elif action == "html_to_markdown":
                # Requires 'html2text' library
                try:
                    converter = html2text.HTML2Text()
                    converter.ignore_links = False
                    md = converter.handle(content)
                    return {"status": "success", "data": {"result": md}}
                except ImportError:
                    return {"status": "error", "error": "html2text library required"}

            return {"status": "error", "error": f"Unsupported action: {action}"}

        except Exception as e:
            return {"status": "error", "error": f"Markdown Node Failed: {str(e)}"}
