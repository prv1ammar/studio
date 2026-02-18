from typing import Any, Dict, Optional, List
from ..base import BaseNode
from ..registry import register_node
import json

@register_node("document_processing_action")
class DocumentProcessingNode(BaseNode):
    """
    Unified Node for Document Processing (CSV, Excel, JSON parsing and transformation).
    """
    node_type = "document_processing_action"
    version = "1.0.0"
    category = "processing"
    credentials_required = []


    properties = [
        {
            'displayName': 'Operation',
            'name': 'operation',
            'type': 'string',
            'default': 'parse_csv',
        },
        {
            'displayName': 'Data',
            'name': 'data',
            'type': 'string',
            'default': '',
        },
        {
            'displayName': 'Delimiter',
            'name': 'delimiter',
            'type': 'string',
            'default': ',',
        },
        {
            'displayName': 'File Path',
            'name': 'file_path',
            'type': 'string',
            'default': '',
        },
        {
            'displayName': 'Has Header',
            'name': 'has_header',
            'type': 'boolean',
            'default': True,
        },
        {
            'displayName': 'Transform Rules',
            'name': 'transform_rules',
            'type': 'string',
            'default': '',
        },
    ]
    inputs = {
        "action": {"type": "string", "default": "parse_csv", "enum": ["parse_csv", "parse_json", "parse_excel", "transform_data"]},
        "file_path": {"type": "string", "optional": True},
        "data": {"type": "any", "optional": True},
        "delimiter": {"type": "string", "default": ","},
        "has_header": {"type": "boolean", "default": True},
        "transform_rules": {"type": "object", "optional": True}
    }
    outputs = {
        "results": {"type": "any"},
        "row_count": {"type": "number"},
        "status": {"type": "string"}
    }

    async def execute(self, input_data: Any, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        try:
            action = self.get_config("action", "parse_csv")
            
            if action == "parse_csv":
                import csv
                import io
                
                file_path = self.get_config("file_path")
                delimiter = self.get_config("delimiter", ",")
                has_header = self.get_config("has_header", True)
                
                if file_path:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                elif isinstance(input_data, str):
                    content = input_data
                else:
                    return {"status": "error", "error": "CSV file path or data is required."}
                
                reader = csv.DictReader(io.StringIO(content), delimiter=delimiter) if has_header else csv.reader(io.StringIO(content), delimiter=delimiter)
                rows = list(reader)
                
                return {
                    "status": "success",
                    "data": {
                        "results": rows,
                        "row_count": len(rows),
                        "columns": list(rows[0].keys()) if has_header and rows else []
                    }
                }
            
            elif action == "parse_json":
                if isinstance(input_data, str):
                    data = json.loads(input_data)
                elif isinstance(input_data, dict):
                    data = input_data
                else:
                    file_path = self.get_config("file_path")
                    if file_path:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            data = json.load(f)
                    else:
                        return {"status": "error", "error": "JSON file path or data is required."}
                
                return {
                    "status": "success",
                    "data": {
                        "results": data,
                        "type": type(data).__name__
                    }
                }
            
            elif action == "transform_data":
                # Simple data transformation
                rules = self.get_config("transform_rules", {})
                data = input_data if input_data else self.get_config("data")
                
                if isinstance(data, list) and rules:
                    transformed = []
                    for item in data:
                        new_item = {}
                        for key, value in rules.items():
                            if isinstance(value, str) and value.startswith("$"):
                                # Reference to original field
                                field_name = value[1:]
                                new_item[key] = item.get(field_name)
                            else:
                                new_item[key] = value
                        transformed.append(new_item)
                    
                    return {
                        "status": "success",
                        "data": {
                            "results": transformed,
                            "row_count": len(transformed)
                        }
                    }
                
                return {"status": "success", "data": {"results": data}}

            return {"status": "error", "error": f"Unsupported action: {action}"}

        except Exception as e:
            return {"status": "error", "error": f"Document Processing Error: {str(e)}"}