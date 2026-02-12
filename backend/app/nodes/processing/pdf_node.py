from ..base import BaseNode
from ..registry import register_node
from typing import Any, Dict, Optional, List
import os
import urllib.parse
import traceback
import uuid
import json

@register_node("pdf_parser")
class PDFParserNode(BaseNode):
    """
    Advanced PDF and Document Parser using Docling.
    Extracts text, tables, and images with structural reconstruction.
    """
    node_type = "pdf_parser"
    version = "1.0.0"
    category = "processing"
    
    inputs = {
        "file_path": {"type": "string", "description": "Absolute path to the document"},
        "ocr_engine": {"type": "string", "enum": ["standard", "easyocr"], "default": "standard"},
        "extract_images": {"type": "boolean", "default": True}
    }
    outputs = {
        "text": {"type": "string", "description": "Reconstructed markdown content"},
        "metadata": {"type": "object"},
        "status": {"type": "string"}
    }

    async def execute(self, input_data: Any = None, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        try:
            # 1. Resolve Input Path
            path = input_data if isinstance(input_data, str) else self.get_config("file_path")
            
            if not path:
                return {"status": "error", "error": "No file path provided."}
            
            # Clean path (handle URL encoding or file:/// prefix)
            path = urllib.parse.unquote(path.replace("file:///", "").replace("file://", ""))
            if os.name == 'nt' and path.startswith("/") and len(path) > 2 and path[1] == ':':
                path = path[1:]
            path = os.path.normpath(path)

            if not os.path.exists(path):
                return {"status": "error", "error": f"File not found at: {path}"}

            # 2. Docling Processing
            from docling.datamodel.base_models import InputFormat
            from docling.document_converter import DocumentConverter, PdfFormatOption
            from docling.datamodel.pipeline_options import PdfPipelineOptions, EasyOcrOptions
            
            pipeline_options = PdfPipelineOptions()
            pipeline_options.do_table_structure = True
            
            if self.get_config("ocr_engine") == "easyocr":
                pipeline_options.do_ocr = True
                pipeline_options.ocr_options = EasyOcrOptions()

            if self.get_config("extract_images", True):
                pipeline_options.images_scale = 2.0
                
            converter = DocumentConverter(
                format_options={
                    InputFormat.PDF: PdfFormatOption(pipeline_options=pipeline_options)
                }
            )
            
            result = converter.convert(path)
            doc = result.document
            
            # 3. Output Directory Setup
            # Resolve project root (backend/app/nodes/processing/ -> 4 levels up to root)
            # Actually use a safer way
            current_dir = os.path.dirname(os.path.abspath(__file__))
            project_root = os.path.abspath(os.path.join(current_dir, "..", "..", "..", ".."))
            output_phys_path = os.path.join(project_root, "outputs", "extracted")
            os.makedirs(output_phys_path, exist_ok=True)
            
            # 4. Content Reconstruction
            markdown_parts = []
            figure_count = 0
            
            for element, level in doc.iterate_items():
                from docling_core.types.doc.labels import DocItemLabel
                
                # Image/Picture handling
                if element.label in [DocItemLabel.PICTURE, DocItemLabel.FORMULA] and self.get_config("extract_images", True):
                    try:
                        figure_count += 1
                        image_filename = f"fig_{uuid.uuid4().hex[:8]}.png"
                        image_path = os.path.join(output_phys_path, image_filename)
                        
                        element.get_image(doc).save(image_path, "PNG")
                        image_url = f"/outputs/extracted/{image_filename}"
                        
                        caption = ""
                        if hasattr(element, "captions") and element.captions:
                             caption = " ".join([c.text for c in element.captions if hasattr(c, "text")])
                        
                        markdown_parts.append(f"\n\n![Figure]({image_url})\n*Caption: {caption}*\n\n")
                    except:
                        pass
                
                # Structural items
                else:
                    try:
                        if element.label == DocItemLabel.TABLE:
                            markdown_parts.append(f"\n\n{element.export_to_markdown()}\n\n")
                        else:
                            text_content = doc.export_to_markdown(item_set={element}).strip()
                            if text_content:
                                markdown_parts.append(text_content + "\n")
                    except:
                        pass

            full_markdown = "".join(markdown_parts)

            return {
                "status": "success",
                "data": {
                    "text": full_markdown,
                    "metadata": {
                        "source": path,
                        "filename": os.path.basename(path),
                        "figure_count": figure_count
                    }
                }
            }
            
        except ImportError:
            return {"status": "error", "error": "Docling dependencies not installed. Please run 'pip install docling'."}
        except Exception as e:
            return {"status": "error", "error": f"PDF Parsing failed: {str(e)}", "traceback": traceback.format_exc()}
