from ...base import BaseNode
from typing import Any, Dict, Optional
import os
import urllib.parse
import traceback
import uuid

class DoclingNode(BaseNode):
    async def execute(self, input_data: Any = None, context: Optional[Dict[str, Any]] = None) -> Any:
        try:
            # Resolve input path
            path = input_data
            
            # Prioritize pulling from handle
            if context and "graph_data" in context:
                graph = context["graph_data"]
                node_id = context["node_id"]
                edges = graph.get("edges", [])
                nodes = graph.get("nodes", [])
                engine = context.get("engine")
                
                path_edge = next((e for e in edges if e["target"] == node_id and e["targetHandle"] == "file_path"), None)
                if path_edge:
                    source_id = path_edge["source"]
                    source_node = next((n for n in nodes if n["id"] == source_id), None)
                    if source_node and engine:
                        path = await engine.execute_node(
                            source_node["data"].get("id"),
                            None,
                            config=source_node["data"],
                            context={**context, "node_id": source_id}
                        )
            
            if isinstance(path, dict):
                path = path.get("file_path") or path.get("path") or path.get("content")
            
            if not path:
                path = self.config.get("path")
            
            if not path:
                return "Error: No file path provided to Docling."
            
            if isinstance(path, list) and path:
                path = path[0]
                
            if isinstance(path, str):
                path = urllib.parse.unquote(path.replace("file:///", "").replace("file://", ""))
                if os.name == 'nt' and path.startswith("/") and len(path) > 2 and path[1] == ':':
                    path = path[1:]
                path = os.path.normpath(path)

            if not os.path.exists(path):
                return f"Error: File not found for Docling at {path}"

            print(f"📄 Docling: Vision Processing {path}...")
            
            from docling.datamodel.base_models import InputFormat
            from docling.document_converter import DocumentConverter, PdfFormatOption
            from docling.datamodel.pipeline_options import PdfPipelineOptions, EasyOcrOptions
            
            pipeline_options = PdfPipelineOptions()
            pipeline_options.do_table_structure = True
            # pipeline_options.do_formula_classification = True
            
            # Detect pipeline mode
            use_vlm = self.config.get("pipeline", "standard") == "vlm"
            
            if use_vlm:
                pipeline_options.do_ocr = True
                pipeline_options.images_scale = 2.0
                pipeline_options.generate_page_images = True
                # pipeline_options.generate_vlm_captions = True
            else:
                if self.config.get("ocr_engine") == "easyocr":
                    pipeline_options.do_ocr = True
                    pipeline_options.ocr_options = EasyOcrOptions()

            # Always enable image extraction if we want to "see" them
            pipeline_options.images_scale = 2.0
                
            converter = DocumentConverter(
                format_options={
                    InputFormat.PDF: PdfFormatOption(pipeline_options=pipeline_options)
                }
            )
            
            result = converter.convert(path)
            doc = result.document
            
            # Setup output paths
            # Setup output paths
            # Go up 5 levels: docling -> tools -> nodes -> app -> backend -> PROJECT_ROOT
            project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", ".."))
            output_web_base = "/outputs"
            output_phys_path = os.path.join(project_root, "outputs")
            os.makedirs(output_phys_path, exist_ok=True)
            
            # --- Intelligent Reconstruction ---
            # We iterate through the items and build a markdown stream with interleaved images
            markdown_parts = []
            figure_count = 0
            
            last_text = ""
            for element, level in doc.iterate_items():
                from docling_core.types.doc.labels import DocItemLabel
                
                # If it's a Picture or Figure
                if element.label in [DocItemLabel.PICTURE, DocItemLabel.FORMULA]:
                    try:
                        figure_count += 1
                        image_filename = f"fig_{uuid.uuid4().hex[:8]}.png"
                        image_path = os.path.join(output_phys_path, image_filename)
                        
                        # Save the image
                        element.get_image(doc).save(image_path, "PNG")
                        image_url = f"http://localhost:8001{output_web_base}/{image_filename}"
                        
                        # Extract Title/Caption
                        # Strategy 1: Check element's own captions
                        caption_text = ""
                        if hasattr(element, "captions") and element.captions:
                             caption_text = " ".join([c.text for c in element.captions if hasattr(c, "text")])
                        
                        # Strategy 2: If no caption in element, use the last short text (likely the title)
                        if not caption_text and last_text and len(last_text) < 200:
                            if "Figure" in last_text or "Graphique" in last_text or "Tableau" in last_text:
                                caption_text = last_text

                        display_caption = f"\n> **Title:** {caption_text}" if caption_text else ""
                        
                        img_markdown = f"\n\n![Graph/Table]({image_url})\n*Visual Context: {element.label} {figure_count}*{display_caption}\n\n"
                        markdown_parts.append(img_markdown)
                        
                    except Exception as e:
                        print(f"⚠️ Docling: Figure save failed: {e}")
                
                # If it's a structural element (Text, Table, Header)
                else:
                    try:
                        if element.label == DocItemLabel.TABLE:
                            markdown_parts.append(f"\n\n{element.export_to_markdown()}\n\n")
                            last_text = "" # Reset after table
                        else:
                            text_content = doc.export_to_markdown(item_set={element}).strip()
                            if text_content:
                                markdown_parts.append(text_content + "\n")
                                last_text = text_content # Store for next image captioning
                    except:
                        pass

            full_markdown = "".join(markdown_parts)

            return [{
                "text": full_markdown,
                "doc_object": doc,
                "metadata": {
                    "source": path,
                    "filename": os.path.basename(path),
                    "has_visuals": figure_count > 0,
                    "figure_count": figure_count
                }
            }]
            
        except Exception as e:
            traceback.print_exc()
            raise e

    async def get_langchain_object(self, context: Optional[Dict[str, Any]] = None) -> Any:
        return None
