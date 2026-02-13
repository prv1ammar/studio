"""
CSV Loader Node - Studio Standard
Batch 35: Document Loaders
"""
from typing import Any, Dict, Optional, List
import pandas as pd
from ...base import BaseNode
from ...registry import register_node

@register_node("csv_loader")
class CSVLoaderNode(BaseNode):
    """
    Load CSV files and covert them to a list of data objects or documents.
    Supports local files and CSV content strings.
    """
    node_type = "csv_loader"
    version = "1.0.0"
    category = "input_output"
    credentials_required = []

    inputs = {
        "file_path": {
            "type": "string",
            "required": True,
            "description": "Path to the CSV file"
        },
        "csv_string": {
            "type": "string",
            "optional": True,
            "description": "Raw CSV content string"
        },
        "delimiter": {
            "type": "string",
            "default": ",",
            "description": "CSV delimiter character"
        },
        "encoding": {
            "type": "string",
            "default": "utf-8",
            "description": "File encoding (utf-8, latin-1, etc.)"
        },
        "text_column": {
            "type": "string",
            "optional": True,
            "description": "Column to use as primary text content (optional)"
        },
        "header": {
            "type": "number",
            "default": 0,
            "description": "Row number to use as header (0-indexed)"
        }
    }

    outputs = {
        "documents": {"type": "array"},
        "data": {"type": "array"},
        "dataframe": {"type": "object"},
        "count": {"type": "number"}
    }

    async def execute(self, input_data: Any, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        try:
            # Get input source
            file_path = self.get_config("file_path")
            csv_string = self.get_config("csv_string")
            delimiter = self.get_config("delimiter", ",")
            encoding = self.get_config("encoding", "utf-8")
            header = int(self.get_config("header", 0))

            # Load data into DataFrame
            if csv_string:
                from io import StringIO
                df = pd.read_csv(StringIO(csv_string), sep=delimiter, encoding=encoding, header=header)
            elif file_path:
                df = pd.read_csv(file_path, sep=delimiter, encoding=encoding, header=header)
            else:
                return {"status": "error", "error": "Provide either file_path or csv_string"}

            # Convert to list of dicts (Data format)
            data_list = df.to_dict(orient="records")

            # Convert to Documents (for RAG)
            text_col = self.get_config("text_column")
            documents = []
            
            for row in data_list:
                # If text column is specified, use it as content
                if text_col and text_col in row:
                    content = str(row[text_col])
                    metadata = {k: v for k, v in row.items() if k != text_col}
                else:
                    # Otherwise, stringify the whole row
                    content = str(row)
                    metadata = row

                documents.append({
                    "text": content,
                    "metadata": metadata
                })

            return {
                "status": "success",
                "data": {
                    "documents": documents,
                    "data": data_list,
                    "count": len(documents),
                    "dataframe": df.to_json()  # Return as JSON for frontend if needed
                }
            }

        except Exception as e:
            return {
                "status": "error",
                "error": f"CSV Loading failed: {str(e)}"
            }
