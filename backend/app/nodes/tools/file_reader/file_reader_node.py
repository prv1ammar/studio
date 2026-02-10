from ...base import BaseNode
from typing import Any, Dict, Optional
import os
import urllib.parse
import traceback

class FileReaderNode(BaseNode):
    async def execute(self, input_data: Any = None, context: Optional[Dict[str, Any]] = None) -> Any:
        try:
            # We treat the input_data as the path if provided, otherwise fallback to config
            path = input_data if isinstance(input_data, str) and input_data.strip() else self.config.get("path")
            if not path: return "Error: No file path provided."
            
            # Path cleanup logic
            path = urllib.parse.unquote(path.replace("file:///", "").replace("file://", ""))
            if os.name == 'nt' and path.startswith("/") and len(path) > 2 and path[1] == ':':
                path = path[1:]
            path = os.path.normpath(path)
            
            if not os.path.exists(path):
                return f"Error: File not found at {path}"
                
            filename = os.path.basename(path)
            clean_name = "".join(c if c.isalnum() else "_" for c in filename.split(".")[0]).lower()
            if not clean_name[0].isalpha(): clean_name = "t_" + clean_name
            
            ext = os.path.splitext(path)[1].lower()
            text = ""
            if ext == ".txt":
                with open(path, "r", encoding="utf-8", errors="ignore") as f:
                    text = f.read()
            elif ext == ".pdf":
                from pypdf import PdfReader
                with open(path, "rb") as f:
                    reader = PdfReader(f)
                    for page in reader.pages:
                        text += (page.extract_text() or "") + "\n"
            elif ext == ".docx":
                import docx
                with open(path, "rb") as f:
                    doc = docx.Document(f)
                    text = "\n".join([para.text for para in doc.paragraphs])
            else:
                return f"Error: Unsupported file extension {ext}"
                
            return {
                "text": text,
                "file_path": path,
                "metadata": {
                    "source": path,
                    "filename": filename
                }
            }
        except Exception as e:
            traceback.print_exc()
            raise e

    async def get_langchain_object(self, context: Optional[Dict[str, Any]] = None) -> Any:
        from langchain.tools import Tool
        
        async def file_tool_func(path: str):
            return await self.execute(input_data=path, context=context)

        return Tool(
            name="file_reader",
            description="Reads the content of a file (.txt, .pdf, .docx). Input should be the full absolute path to the file.",
            func=file_tool_func
        )
