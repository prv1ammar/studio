from typing import Any, Dict, Optional, List
from ..base import BaseNode
from ..registry import register_node
import os

@register_node("legal_action")
class LegalNode(BaseNode):
    """
    Vertical Node for Legal Automation.
    Specialized in analyzing legal documents, checking compliance, and assessing risk using AI.
    """
    node_type = "legal_action"
    version = "1.0.0"
    category = "verticals"
    credentials_required = ["openai_auth"]


    properties = [
        {
            'displayName': 'Document Text',
            'name': 'document_text',
            'type': 'string',
            'default': '',
            'description': 'Legal text to analyze',
        },
        {
            'displayName': 'Jurisdiction',
            'name': 'jurisdiction',
            'type': 'string',
            'default': 'US',
        },
        {
            'displayName': 'Operation',
            'name': 'operation',
            'type': 'string',
            'default': 'contract_analysis',
        },
    ]
    inputs = {
        "operation": {"type": "string", "default": "contract_analysis", "enum": ["contract_analysis", "compliance_check", "risk_assessment"]},
        "jurisdiction": {"type": "string", "default": "US", "enum": ["US", "EU", "UK", "Middle East"]},
        "document_text": {"type": "string", "description": "Legal text to analyze"}
    }
    outputs = {
        "analysis": {"type": "string"},
        "risk_level": {"type": "string"},
        "status": {"type": "string"}
    }

    async def execute(self, input_data: Any, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        try:
            from openai import AsyncOpenAI
            
            # 1. Resolve Auth
            creds = await self.get_credential("openai_auth")
            api_key = creds.get("api_key") if creds else os.getenv("OPENAI_API_KEY")
            
            if not api_key:
                return {"status": "error", "error": "OpenAI API Key is required for Legal AI."}

            client = AsyncOpenAI(api_key=api_key)
            op = self.get_config("operation", "contract_analysis")
            jurisdiction = self.get_config("jurisdiction", "US")
            text = str(input_data) if isinstance(input_data, str) else self.get_config("document_text", "")

            if not text:
                return {"status": "error", "error": "Legal document text is required."}

            system_prompt = f"You are an expert Legal AI Assistant specialized in {jurisdiction} Law. Perform {op}."
            
            response = await client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Analyze this text:\n{text}"}
                ],
                temperature=0.1
            )
            
            result_text = response.choices[0].message.content
            
            return {
                "status": "success",
                "data": {
                    "analysis": result_text,
                    "operation": op,
                    "jurisdiction": jurisdiction
                }
            }

        except Exception as e:
            return {"status": "error", "error": f"Legal Node Error: {str(e)}"}