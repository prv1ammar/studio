from typing import Any, Dict, Optional
from ..base import BaseNode
from ..models.litellm.litellm_node import LiteLLMNode
from ..registry import register_node
import json

@register_node("ai_extractor")
class AIExtractorNode(BaseNode):
    """
    Generalized AI Structured Data Extractor.
    Extracts specific fields from unstructured text using an LLM and a JSON schema.
    """
    node_type = "ai_extractor"
    version = "1.0.0"
    category = "processing"

    inputs = {
        "text_content": {"type": "string", "description": "Text to extract from"},
        "schema": {"type": "string", "description": "JSON schema for extraction (dict or string)"},
        "instruction": {"type": "string", "default": "Extract the following information from the text."}
    }
    outputs = {
        "data": {"type": "object"},
        "status": {"type": "string"}
    }
    
    async def execute(self, input_data: Any, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        # 1. Resolve Input Text
        text_content = str(input_data) if input_data else self.get_config("text_content")
        if isinstance(input_data, dict):
            text_content = input_data.get("markdown") or input_data.get("text") or text_content
        
        if not text_content:
            return {"status": "error", "error": "No input text provided."}

        # 2. Resolve Extraction Schema
        schema_cfg = self.get_config("schema", "{}")
        try:
            schema = json.loads(schema_cfg) if isinstance(schema_cfg, str) else schema_cfg
        except:
             return {"status": "error", "error": "Invalid JSON schema configuration."}

        if not schema:
            return {"status": "error", "error": "No extraction schema defined."}

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
            llm_node = LiteLLMNode(config=self.config)
            llm = await llm_node.get_langchain_object(context)
            
            response = await llm.ainvoke(prompt)
            result_text = response.content if hasattr(response, 'content') else str(response)
            
            # Clean markdown JSON blocks
            result_text = result_text.strip()
            if "```" in result_text:
                result_text = result_text.split("```")[1]
                if result_text.lower().startswith("json"):
                    result_text = result_text[4:]
            
            extracted_data = json.loads(result_text.strip())
            
            return {
                "status": "success",
                "data": {
                    "extracted_data": extracted_data,
                    "raw_length": len(text_content)
                }
            }
            
        except Exception as e:
            return {"status": "error", "error": f"AI Extraction Failed: {str(e)}"}
