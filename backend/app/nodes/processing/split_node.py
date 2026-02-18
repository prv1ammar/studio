from ..base import BaseNode
from ..registry import register_node
from typing import Any, Dict, Optional, List
from langchain_text_splitters import RecursiveCharacterTextSplitter

@register_node("text_splitter")
class SplitTextNode(BaseNode):
    """
    Splits long text into smaller chunks for LLM processing or vector storage.
    """
    node_type = "text_splitter"
    version = "1.0.0"
    category = "processing"


    properties = [
        {
            'displayName': 'Chunk Overlap',
            'name': 'chunk_overlap',
            'type': 'string',
            'default': 200,
        },
        {
            'displayName': 'Chunk Size',
            'name': 'chunk_size',
            'type': 'string',
            'default': 1000,
        },
        {
            'displayName': 'Text',
            'name': 'text',
            'type': 'string',
            'default': '',
            'description': 'Text to split',
        },
    ]
    inputs = {
        "chunk_size": {"type": "number", "default": 1000},
        "chunk_overlap": {"type": "number", "default": 200},
        "text": {"type": "string", "description": "Text to split"}
    }
    outputs = {
        "chunks": {"type": "array"},
        "count": {"type": "number"},
        "status": {"type": "string"}
    }

    async def execute(self, input_data: Any = None, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        try:
            data_to_split = input_data if input_data is not None else self.get_config("text")
            
            if not data_to_split:
                return {"status": "error", "error": "No text provided to SplitTextNode.", "data": None}
                
            chunk_size = int(self.get_config("chunk_size", 1000))
            chunk_overlap = int(self.get_config("chunk_overlap", 200))
            
            splitter = RecursiveCharacterTextSplitter(
                chunk_size=chunk_size,
                chunk_overlap=chunk_overlap
            )
            
            # Normalize to list if necessary, but usually we split a string
            if isinstance(data_to_split, list):
                # Flatten or handle list of items
                combined_results = []
                for item in data_to_split:
                    content = item.get("text") if isinstance(item, dict) else str(item)
                    metadata = item.get("metadata", {}) if isinstance(item, dict) else {}
                    chunks = splitter.split_text(content)
                    for i, chunk in enumerate(chunks):
                        combined_results.append({
                            "text": chunk,
                            "metadata": {**metadata, "chunk_index": i}
                        })
                results = combined_results
            else:
                chunks = splitter.split_text(str(data_to_split))
                results = [{"text": chunk, "metadata": {"chunk_index": i}} for i, chunk in enumerate(chunks)]
            
            return {
                "status": "success",
                "data": {
                    "chunks": results,
                    "count": len(results)
                }
            }
            
        except Exception as e:
            return {"status": "error", "error": f"Splitting Failed: {str(e)}", "data": None}