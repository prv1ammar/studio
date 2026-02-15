"""
Spreadsheet Parser Node - Studio Standard (Universal Method)
Batch 111: Utilities & Data Processing
"""
from typing import Any, Dict, Optional
import csv
import json
import io
# import pandas as pd # Optional, but heavy. Using pure python libs for CSV.
# For XLSX, openpyxl is needed. We will implement CSV support fully and placeholder for XLSX/Pandas if not installed.

from ...base import BaseNode
from ...registry import register_node

@register_node("spreadsheet_parser_node")
class SpreadsheetParserNode(BaseNode):
    """
    Parse CSV, JSON, and (optionally) XLSX data.
    """
    node_type = "spreadsheet_parser_node"
    version = "1.0.0"
    category = "utilities"
    credentials_required = []

    inputs = {
        "action": {
            "type": "dropdown",
            "default": "parse",
            "options": ["parse", "stringify"],
            "description": "Parse (String -> JSON) or Stringify (JSON -> String)"
        },
        "format": {
            "type": "dropdown",
            "default": "csv",
            "options": ["csv", "json"], # xlsx omitted unless implemented with binary logic
            "description": "Data Format"
        },
        "content": {
            "type": "string",
            "optional": True
        },
        "delimiter": {
            "type": "string",
            "default": ",",
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
            action = self.get_config("action", "parse")
            format = self.get_config("format", "csv")
            delimiter = self.get_config("delimiter", ",")
            
            if action == "parse":
                if format == "json":
                    try:
                        data = json.loads(content)
                        return {"status": "success", "data": {"result": data}}
                    except:
                        return {"status": "error", "error": "Invalid JSON"}
                
                elif format == "csv":
                    f = io.StringIO(content)
                    reader = csv.DictReader(f, delimiter=delimiter)
                    data = list(reader)
                    return {"status": "success", "data": {"result": data}}

            elif action == "stringify":
                # input expected to be list of dicts or dict
                try:
                    data = json.loads(content) if isinstance(content, str) else content
                except:
                    data = content # Assume list/dict object
                
                if format == "json":
                     return {"status": "success", "data": {"result": json.dumps(data)}}
                
                elif format == "csv":
                    if not isinstance(data, list) or not data:
                        return {"status": "error", "error": "CSV stringify requires a list of objects"}
                    
                    output = io.StringIO()
                    fieldnames = data[0].keys()
                    writer = csv.DictWriter(output, fieldnames=fieldnames, delimiter=delimiter)
                    writer.writeheader()
                    writer.writerows(data)
                    return {"status": "success", "data": {"result": output.getvalue()}}

            return {"status": "error", "error": f"Unsupported action: {action}"}

        except Exception as e:
            return {"status": "error", "error": f"Spreadsheet Parser Failed: {str(e)}"}
