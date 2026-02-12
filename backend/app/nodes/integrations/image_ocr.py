from ..base import BaseNode
from ..registry import register_node
from typing import Any, Dict, Optional, List
import json

@register_node("image_ocr")
class ImageOCRNode(BaseNode):
    """
    Visual OCR (VOCR) using JigsawStack.
    Extracts structured data from images and documents using target prompts.
    """
    node_type = "image_ocr"
    version = "1.0.0"
    category = "integrations"
    credentials_required = ["jigsawstack_api_key"]
    
    inputs = {
        "url": {"type": "string", "description": "URL of the image or document"},
        "prompts": {"type": "string", "description": "Describe what to extract (comma separated)"},
        "page_range": {"type": "string", "description": "e.g. '1-3' (optional)"}
    }
    outputs = {
        "data": {"type": "object"},
        "summary": {"type": "string"},
        "status": {"type": "string"}
    }

    async def execute(self, input_data: Any = None, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        try:
            # 1. Auth Retrieval
            creds = await self.get_credential("jigsawstack_api_key")
            api_key = creds.get("api_key") if creds else self.get_config("api_key")
            
            if not api_key:
                return {"status": "error", "error": "JigsawStack API Key is required."}

            # 2. Setup Client
            from jigsawstack import JigsawStack, JigsawStackError
            client = JigsawStack(api_key=api_key)

            # 3. Build Request
            url = input_data if isinstance(input_data, str) and input_data.startswith("http") else self.get_config("url")
            prompts_str = self.get_config("prompts", "Describe the image in detail")
            
            params = {
                "url": url,
                "prompt": [p.strip() for p in prompts_str.split(",")] if "," in prompts_str else [prompts_str]
            }

            page_range = self.get_config("page_range")
            if page_range and "-" in page_range:
                try:
                    start, end = page_range.split("-")
                    params["page_range"] = [int(start), int(end)]
                except:
                    pass

            if not url:
                return {"status": "error", "error": "Image URL is required."}

            # 4. Call API
            response = client.vision.vocr(params)

            if not response.get("success", False):
                return {"status": "error", "error": "JigsawStack API returned unsuccessful response", "data": response}

            return {
                "status": "success",
                "data": {
                    "data": response.get("context") or response,
                    "summary": response.get("description", "")
                }
            }

        except ImportError:
            return {"status": "error", "error": "jigsawstack library not installed. Run 'pip install jigsawstack'."}
        except JigsawStackError as e:
            return {"status": "error", "error": f"JigsawStack Error: {str(e)}"}
        except Exception as e:
            return {"status": "error", "error": f"VOCR Node Failed: {str(e)}"}
