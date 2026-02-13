"""
Text Splitter Node - Studio Standard
Batch 34: Text Processing Nodes
"""
from typing import Any, Dict, Optional, List
from ...base import BaseNode
from ...registry import register_node

@register_node("text_splitter")
class TextSplitterNode(BaseNode):
    """
    Split text into chunks using various strategies (Character, Recursive, Token).
    Essential for RAG applications to prepare text for embedding.
    """
    node_type = "text_splitter"
    version = "2.0.0"
    category = "text_processing"
    credentials_required = []

    inputs = {
        "text": {
            "type": "string",
            "required": True,
            "description": "Text or documents to split"
        },
        "splitter_type": {
            "type": "dropdown",
            "default": "Recursive Character",
            "options": [
                "Recursive Character",
                "Character",
                "Token",
                "Markdown"
            ],
            "description": "Strategy for splitting text"
        },
        "chunk_size": {
            "type": "number",
            "default": 1000,
            "description": "Maximum size of each chunk"
        },
        "chunk_overlap": {
            "type": "number",
            "default": 200,
            "description": "Overlap between chunks to maintain context"
        },
        "separator": {
            "type": "string",
            "default": "\n\n",
            "description": "Primary separator (for Character splitter)"
        }
    }

    outputs = {
        "chunks": {"type": "array"},
        "documents": {"type": "array"},
        "count": {"type": "number"}
    }

    async def execute(self, input_data: Any, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        try:
            # Import dependencies
            try:
                from langchain_text_splitters import (
                    RecursiveCharacterTextSplitter,
                    CharacterTextSplitter,
                    TokenTextSplitter,
                    MarkdownHeaderTextSplitter
                )
                from langchain_core.documents import Document
            except ImportError:
                return {
                    "status": "error",
                    "error": "langchain-text-splitters not installed. Run: pip install langchain-text-splitters"
                }

            # Get inputs
            text_input = input_data if input_data is not None else self.get_config("text")
            
            if not text_input:
                return {"status": "error", "error": "No text provided to split"}

            # Get configuration
            splitter_type = self.get_config("splitter_type", "Recursive Character")
            chunk_size = int(self.get_config("chunk_size", 1000))
            chunk_overlap = int(self.get_config("chunk_overlap", 200))
            separator = self.get_config("separator", "\n\n")

            # Validate config
            if chunk_overlap >= chunk_size:
                return {"status": "error", "error": "Chunk overlap must be smaller than chunk size"}

            # Prepare documents
            docs = []
            if isinstance(text_input, list):
                for item in text_input:
                    if isinstance(item, Document):
                        docs.append(item)
                    elif isinstance(item, dict) and "text" in item:
                        docs.append(Document(
                            page_content=item["text"],
                            metadata=item.get("metadata", {})
                        ))
                    else:
                        docs.append(Document(page_content=str(item)))
            elif isinstance(text_input, Document):
                docs = [text_input]
            elif isinstance(text_input, dict) and "text" in text_input:
                docs = [Document(
                    page_content=text_input["text"],
                    metadata=text_input.get("metadata", {})
                )]
            else:
                docs = [Document(page_content=str(text_input))]

            # Choose splitter based on type
            if splitter_type == "Recursive Character":
                splitter = RecursiveCharacterTextSplitter(
                    chunk_size=chunk_size,
                    chunk_overlap=chunk_overlap,
                    separators=["\n\n", "\n", " ", ""]
                )
            elif splitter_type == "Character":
                splitter = CharacterTextSplitter(
                    separator=separator,
                    chunk_size=chunk_size,
                    chunk_overlap=chunk_overlap
                )
            elif splitter_type == "Token":
                splitter = TokenTextSplitter(
                    chunk_size=chunk_size,
                    chunk_overlap=chunk_overlap
                )
            elif splitter_type == "Markdown":
                # Markdown splitting is special - it splits by headers
                headers_to_split_on = [
                    ("#", "Header 1"),
                    ("##", "Header 2"),
                    ("###", "Header 3"),
                ]
                splitter = MarkdownHeaderTextSplitter(headers_to_split_on=headers_to_split_on)
                # Note: Markdown splitter doesn't use chunk_size directly in init
                # We often need to chain it with RecursiveCharacterTextSplitter
                
            # Perform splitting
            split_docs = splitter.split_documents(docs)

            # Format output
            chunks = [doc.page_content for doc in split_docs]
            output_docs = [
                {
                    "text": doc.page_content,
                    "metadata": doc.metadata
                }
                for doc in split_docs
            ]

            return {
                "status": "success",
                "data": {
                    "chunks": chunks,
                    "documents": output_docs,
                    "count": len(chunks),
                    "splitter_used": splitter_type
                }
            }

        except Exception as e:
            return {
                "status": "error",
                "error": f"Text Splitter error: {str(e)}"
            }
