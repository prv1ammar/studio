"""
Split Text Node - Studio Standard
Batch 34: Text Processing Nodes
"""
from typing import Any, Dict, Optional, List
from ...base import BaseNode
from ...registry import register_node

@register_node("split_text")
class SplitTextNode(BaseNode):
    """
    Split text into chunks based on specified criteria.
    Essential for document preprocessing and RAG applications.
    """
    node_type = "split_text"
    version = "1.0.0"
    category = "text_processing"
    credentials_required = []

    inputs = {
        "text": {
            "type": "string",
            "required": True,
            "description": "Text to split into chunks"
        },
        "chunk_size": {
            "type": "number",
            "default": 1000,
            "description": "Maximum length of each chunk"
        },
        "chunk_overlap": {
            "type": "number",
            "default": 200,
            "description": "Number of characters to overlap between chunks"
        },
        "separator": {
            "type": "string",
            "default": "\n",
            "description": "Character to split on (\\n for newline, \\n\\n for paragraphs)"
        },
        "keep_separator": {
            "type": "dropdown",
            "default": "False",
            "options": ["False", "True", "Start", "End"],
            "description": "Whether to keep the separator and where to place it"
        }
    }

    outputs = {
        "chunks": {"type": "array"},
        "count": {"type": "number"},
        "metadata": {"type": "array"}
    }

    async def execute(self, input_data: Any, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        try:
            # Import dependencies
            try:
                from langchain_text_splitters import CharacterTextSplitter
                from langchain_core.documents import Document
            except ImportError:
                return {
                    "status": "error",
                    "error": "langchain-text-splitters not installed. Run: pip install langchain-text-splitters"
                }

            # Get text from input
            text = input_data if isinstance(input_data, str) else self.get_config("text", "")
            
            if not text:
                return {"status": "error", "error": "Text is required"}

            # Get configuration
            chunk_size = int(self.get_config("chunk_size", 1000))
            chunk_overlap = int(self.get_config("chunk_overlap", 200))
            separator = self._fix_separator(self.get_config("separator", "\n"))
            keep_separator = self._parse_keep_separator(self.get_config("keep_separator", "False"))

            # Validate configuration
            if chunk_overlap >= chunk_size:
                return {
                    "status": "error",
                    "error": "Chunk overlap must be less than chunk size"
                }

            # Create text splitter
            splitter = CharacterTextSplitter(
                chunk_size=chunk_size,
                chunk_overlap=chunk_overlap,
                separator=separator,
                keep_separator=keep_separator
            )

            # Convert text to document for splitting
            if isinstance(input_data, dict) and "text" in input_data:
                doc = Document(
                    page_content=input_data["text"],
                    metadata=input_data.get("metadata", {})
                )
                docs = [doc]
            else:
                docs = [Document(page_content=text)]

            # Split documents
            split_docs = splitter.split_documents(docs)

            # Convert to output format
            chunks = [doc.page_content for doc in split_docs]
            metadata = [doc.metadata for doc in split_docs]

            return {
                "status": "success",
                "data": {
                    "chunks": chunks,
                    "count": len(chunks),
                    "metadata": metadata
                }
            }

        except Exception as e:
            return {
                "status": "error",
                "error": f"Split Text error: {str(e)}"
            }

    def _fix_separator(self, separator: str) -> str:
        """Fix common separator issues and convert to proper format."""
        # Handle common mistakes
        if separator == "/n":
            return "\n"
        if separator == "/t":
            return "\t"
        
        # Unescape string (convert \\n to \n, etc.)
        try:
            return separator.encode().decode('unicode_escape')
        except:
            return separator

    def _parse_keep_separator(self, keep_sep: Any) -> Any:
        """Parse keep_separator value to proper format."""
        if isinstance(keep_sep, str):
            if keep_sep.lower() == "false":
                return False
            elif keep_sep.lower() == "true":
                return True
            # 'start' and 'end' are kept as strings
        return keep_sep
