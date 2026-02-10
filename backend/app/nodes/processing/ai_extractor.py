from typing import Any, Dict, Optional
from ..base import BaseNode
from ..models.litellm.litellm_node import LiteLLMNode
from ..registry import register_node
import json

@register_node("aiExtractorNode")
class AIExtractorNode(BaseNode):
    """
    Generalized AI Structured Data Extractor.
    Uses LLM to extract specific fields from unstructured text (Markdown, Chat, Scraped content).
    """
    
    async def execute(self, input_data: Any, context: Optional[Dict[str, Any]] = None) -> Any:
        # 1. Resolve Input Text
        text_content = None
        if isinstance(input_data, str):
            text_content = input_data
        elif isinstance(input_data, dict):
            # Try common fields
            text_content = input_data.get("markdown") or input_data.get("text") or input_data.get("input") or str(input_data)
        
        if not text_content:
            text_content = self.get_config("text_content")
            
        if not text_content:
            return {"error": "No input text provided", "status": "failed"}

        # 2. Resolve Extraction Schema
        # Example schema: {"price": "number", "location": "string", "urgent": "boolean"}
        schema_str = self.get_config("schema", "{}")
        try:
            if isinstance(schema_str, str):
                schema = json.loads(schema_str)
            else:
                schema = schema_str
        except:
             return {"error": "Invalid JSON schema configuration", "status": "failed"}

        if not schema:
            return {"error": "No extraction schema defined", "status": "failed"}

        # 3. Build Prompt
        instruction = self.get_config("instruction", "Extract the following information from the text.")
        
        prompt = f"""{instruction}

Target Schema:
{json.dumps(schema, indent=2)}

Input Text:
---
{text_content}
---

Respond ONLY with valid JSON matching the schema. If a value is missing, use null.
"""

        # 4. Execute LLM
        try:
            # Use LiteLLMNode helper
            llm_node = LiteLLMNode(config=self.config)
            llm = await llm_node.get_langchain_object(context)
            
            response = llm.invoke(prompt)
            result_text = response.content if hasattr(response, 'content') else str(response)
            
            # Clean possible markdown block
            result_text = result_text.strip()
            if result_text.startswith("```"):
                result_text = result_text.split("```")[1]
                if result_text.lower().startswith("json"):
                    result_text = result_text[4:]
            
            extracted_data = json.loads(result_text.strip())
            
            return {
                "extracted_data": extracted_data,
                "status": "success",
                "raw_text_length": len(text_content)
            }
            
        except Exception as e:
            return {"error": str(e), "status": "failed"}

    async def get_langchain_object(self, context: Optional[Dict[str, Any]] = None) -> Any:
        return None
