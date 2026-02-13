"""
PDF Loader Node - Studio Standard
Batch 35: Document Loaders
"""
from typing import Any, Dict, Optional, List
import os
from ...base import BaseNode
from ...registry import register_node

@register_node("pdf_loader")
class PDFLoaderNode(BaseNode):
    """
    Load and parse PDF files into documents.
    Supports PyPayPDF and Unstructured loaders.
    """
    node_type = "pdf_loader"
    version = "1.0.0"
    category = "input_output"
    credentials_required = []

    inputs = {
        "file_path": {
            "type": "string",
            "required": True,
            "description": "Path to the PDF file"
        },
        "loader_type": {
            "type": "dropdown",
            "default": "PyPDF",
            "options": ["PyPDF", "Unstructured", "PyMuPDF"],
            "description": "Library to use for PDF parsing"
        },
        "extract_images": {
            "type": "boolean",
            "default": False,
            "description": "Extract images from the PDF (Unstructured only)"
        }
    }

    outputs = {
        "documents": {"type": "array"},
        "text": {"type": "string"},
        "metadata": {"type": "object"}
    }

    async def execute(self, input_data: Any, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        try:
            # Import dependencies based on loader type
            loader_type = self.get_config("loader_type", "PyPDF")
            
            # Get file path
            file_path = input_data if isinstance(input_data, str) else self.get_config("file_path")
            
            if not file_path:
                return {"status": "error", "error": "File path is required"}

            # Resolve path (handle relative paths)
            file_path = os.path.abspath(file_path)
            
            if not os.path.exists(file_path):
                return {"status": "error", "error": f"File not found: {file_path}"}

            # Select loader
            if loader_type == "PyPDF":
                try:
                    from langchain_community.document_loaders import PyPDFLoader
                    loader = PyPDFLoader(file_path)
                except ImportError:
                    return {"status": "error", "error": "pypdf not installed. Run: pip install pypdf"}

            elif loader_type == "PyMuPDF":
                try:
                    from langchain_community.document_loaders import PyMuPDFLoader
                    loader = PyMuPDFLoader(file_path)
                except ImportError:
                    return {"status": "error", "error": "pymupdf not installed. Run: pip install pymupdf"}

            elif loader_type == "Unstructured":
                try:
                    from langchain_community.document_loaders import UnstructuredPDFLoader
                    mode = "elements" if self.get_config("extract_images") else "single"
                    loader = UnstructuredPDFLoader(file_path, mode=mode)
                except ImportError:
                    return {"status": "error", "error": "unstructured not installed. Run: pip install unstructured"}
            else:
                return {"status": "error", "error": f"Unknown loader type: {loader_type}"}

            # Load documents
            docs = loader.load()

            # Format output
            full_text = "\n\n".join([doc.page_content for doc in docs])
            
            output_docs = [
                {
                    "text": doc.page_content,
                    "metadata": doc.metadata
                }
                for doc in docs
            ]

            return {
                "status": "success",
                "data": {
                    "documents": output_docs,
                    "text": full_text,
                    "metadata": {
                        "source": file_path,
                        "pages": len(docs),
                        "filename": os.path.basename(file_path)
                    }
                }
            }

        except Exception as e:
            return {
                "status": "error",
                "error": f"PDF Loading failed: {str(e)}"
            }
